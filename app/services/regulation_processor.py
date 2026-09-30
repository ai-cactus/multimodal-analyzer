"""
Regulation processing workflow
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, date
from typing import Optional
from uuid import UUID
import os

from app.models import RegulationDocument, RegulationText, ComplianceBody
from app.services.document_ai import DocumentAIExtractor
from app.services.section_parser import ComplianceBodySectionParser
from app.services.embedding import get_embedding_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegulationProcessor:
    """
    Service for processing and ingesting regulation manuals
    """
    
    def __init__(self):
        self.doc_ai = DocumentAIExtractor()
        self.embedding_service = get_embedding_service()
    
    async def process_regulation(
        self,
        db: AsyncSession,
        regulation_id: UUID,
        file_path: str,
        compliance_body_id: int,
        version: str,
        effective_date: Optional[date] = None
    ):
        """
        Process regulation document: extract, chunk, embed, and store
        
        Args:
            db: Database session
            regulation_id: UUID of the regulation document
            file_path: Path to the uploaded regulation file
            compliance_body_id: ID of the compliance body
            version: Version string
            effective_date: Effective date of the regulation
        """
        try:
            logger.info(f"Starting regulation processing: {regulation_id}")
            
            # Get compliance body
            result = await db.execute(
                select(ComplianceBody).where(ComplianceBody.id == compliance_body_id)
            )
            compliance_body = result.scalar_one_or_none()
            
            if not compliance_body:
                raise ValueError(f"Compliance body {compliance_body_id} not found")
            
            # Step 1: Extract text using Document AI
            logger.info("Extracting text with Document AI...")
            extracted_data = await self.doc_ai.extract_document(
                file_path,
                mime_type=self._get_mime_type(file_path)
            )
            
            # Get full text from extraction
            full_text = self._extract_full_text(extracted_data, file_path)
            logger.info(f"Extracted {len(full_text)} characters of text from regulation manual")
            
            # Update regulation document with total pages
            await db.execute(
                update(RegulationDocument)
                .where(RegulationDocument.id == regulation_id)
                .values(total_pages=extracted_data["total_pages"])
            )
            await db.commit()
            
            # Step 2: Parse sections using compliance body parser
            logger.info(f"Parsing sections for {compliance_body.name}...")
            parser = ComplianceBodySectionParser(compliance_body.name)
            chunks = parser.chunk_by_section(full_text, max_chunk_words=1000)
            
            logger.info(f"Created {len(chunks)} chunks from regulation manual")
            
            if not chunks:
                logger.warning(f"No chunks created for regulation {regulation_id}. text length: {len(full_text)}")
            
            # Step 3: Generate embeddings
            if chunks:
                logger.info("Generating embeddings...")
                chunk_texts = [chunk['text'] for chunk in chunks]
                embeddings = await self.embedding_service.generate_embeddings_batch(
                    chunk_texts,
                    task_type="RETRIEVAL_DOCUMENT",
                    batch_size=50
                )
            else:
                embeddings = []
            
            # Step 4: Store regulation texts with embeddings
            logger.info("Storing regulation texts...")
            regulation_texts = []
            
            for chunk, embedding in zip(chunks, embeddings):
                reg_text = RegulationText(
                    regulation_id=regulation_id,
                    section_ref=chunk['section_ref'],
                    text=chunk['text'],
                    embedding_v2=embedding,
                    meta={
                        'sub_chunk': chunk['sub_chunk'],
                        'word_count': chunk['word_count'],
                        'compliance_body': chunk['compliance_body']
                    }
                )
                regulation_texts.append(reg_text)
            
            if chunks:
                db.add_all(regulation_texts)
                
                # Step 5: Update regulation status to completed
                await db.execute(
                    update(RegulationDocument)
                    .where(RegulationDocument.id == regulation_id)
                    .values(
                        status="completed",
                        completed_at=datetime.utcnow()
                    )
                )
                await db.commit()
                logger.info(f"Successfully processed regulation {regulation_id}: {len(regulation_texts)} chunks stored")
                
                # Clean up uploaded file only on success
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
            else:
                logger.error(f"Failed to create any chunks for regulation {regulation_id}. Marking as failed.")
                await db.execute(
                    update(RegulationDocument)
                    .where(RegulationDocument.id == regulation_id)
                    .values(status="failed", meta={"error": "No text extracted or chunks created"})
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error processing regulation {regulation_id}: {e}", exc_info=True)
            
            # Update status to failed
            await db.execute(
                update(RegulationDocument)
                .where(RegulationDocument.id == regulation_id)
                .values(status="failed", meta={"error": str(e)})
            )
            await db.commit()
            
            raise
    
    def _extract_full_text(self, extracted_data: dict, file_path: str) -> str:
        """
        Extract full text from Document AI output, with native PDF fallback
        """
        full_text = ""
        
        # 1. Try Document AI pre-consolidated full_text
        if "full_text" in extracted_data and len(extracted_data["full_text"].strip()) > 100:
            full_text = extracted_data["full_text"]
        
        # 2. Try raw_layout text
        if not full_text:
            raw_layout = extracted_data.get("raw_layout")
            if raw_layout and hasattr(raw_layout, 'text') and len(raw_layout.text.strip()) > 100:
                full_text = raw_layout.text

        # 3. Native PDF fallback if PDF
        if not full_text:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                logger.info(f"Document AI extracted minimal text for {file_path}. Using native PDF fallback.")
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    text_parts = []
                    for page in reader.pages:
                        text_parts.append(page.extract_text() or "")
                    full_text = "\n".join(text_parts)
                    logger.info(f"Native extraction successful: {len(full_text)} characters")
                except Exception as e:
                    logger.error(f"Native PDF extraction failed: {e}")
        
        return full_text
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain'
        }
        
        return mime_types.get(ext, 'application/pdf')
