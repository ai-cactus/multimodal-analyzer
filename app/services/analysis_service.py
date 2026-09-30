"""
Document Analysis Service - Orchestrates full workflow
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text, func
from datetime import datetime
from typing import Optional, List
import os
from uuid import UUID
import asyncio

from app.models import UploadedDocument, DocumentElement, RegulationDocument, RegulationText, ComplianceBody
from app.services.embedding import get_embedding_service
from app.services.document_ai import DocumentAIExtractor
from app.services.llm_client import get_llm_client
from app.services.consensus_engine import get_consensus_engine
from app.services.cost_tracker import CostTracker
from app.prompts.templates import get_analysis_prompt, REDRAFT_PROMPT, QUALITY_SCORE_PROMPT, REPORT_SYNTHESIS_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentAnalysisService:
    """
    Orchestrates the complete document analysis workflow
    """
    
    def __init__(self):
        self.doc_ai = DocumentAIExtractor()
        self.llm_client = get_llm_client()
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent LLM calls
    
    async def analyze_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        file_path: str,
        compliance_body: str,
        compliance_section: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Execute full analysis workflow
        
        Steps:
        1. Extract elements with Document AI
        2. For each element:
           a. Retrieve relevant regulations  
           b. Multi-LLM analysis
        3. Build consensus
        4. Dual redrafting
        5. Verification
        6. Generate reports
        """
        try:
            logger.info(f"Starting analysis for document {document_id}")
            
            # Initialize cost tracker if not provided
            if cost_tracker is None:
                cost_tracker = CostTracker(document_id=str(document_id))
            
            # Fetch document record to ensure it exists and get metadata
            result = await db.execute(
                select(UploadedDocument).where(UploadedDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Document {document_id} not found in database. Aborting analysis.")
                return

            # Update status
            await self._update_status(db, document_id, "extracting", "Extracting document structure")
            
            # Step 1: Extract document structure
            extracted_data = await self.doc_ai.extract_document(
                file_path,
                mime_type=self._get_mime_type(file_path),
                cost_tracker=cost_tracker,
            )
            
            elements = extracted_data['elements']
            full_text = extracted_data.get('full_text', '')
            logger.info(f"Extracted {len(elements)} elements")
            
            # Retrieve regulations using semantic search with document content
            # Use first 2000 chars of full_text as query for relevance
            query_sample = full_text[:2000] if full_text else ""
            regulations = await self._retrieve_regulations(
                db, compliance_body, compliance_section, query_text=query_sample, top_k=10
            )
            
            # Check if regulations were found
            if not regulations:
                logger.warning(f"No regulations found for {compliance_body}. Analysis may be limited.")
                regulations = f"Note: No specific {compliance_body} regulations were found in the database. Please upload the regulation manual first."
            
            if not elements:
                logger.warning(f"No elements extracted from document {document_id}")
                
                # Check if we at least have full text
                if full_text and len(full_text.strip()) > 50:
                    logger.info("Found substantial text despite no structured elements. Creating fallback element.")
                    # Create a single virtual element for the whole document
                    elements = [{
                        "element_id": f"virtual_text_{document_id}",
                        "element_type": "text",
                        "page_number": 1,
                        "order_index": 0,
                        "content": {"text": full_text},
                        "section_path": "Full Document",
                        "bounding_box": None
                    }]
                else:
                    await db.execute(
                        update(UploadedDocument)
                        .where(UploadedDocument.id == document_id)
                        .values(
                            status="completed",
                            completed_at=datetime.utcnow(),
                            meta={
                                "high_confidence_count": 0,
                                "medium_confidence_count": 0,
                                "total_elements": 0,
                                "message": "No structured elements or readable text found in document."
                            }
                        )
                    )
                    await db.commit()
                    return

            # Store elements in database
            for elem in elements:
                doc_element = DocumentElement(
                    document_id=document_id,
                    element_type=elem['element_type'],
                    page_number=elem['page_number'],
                    order_index=elem['order_index'],
                    section_path=elem.get('section_path'),
                    bounding_box=elem.get('bounding_box'),
                    content=elem['content'],
                    raw_docai_output=elem
                )
                db.add(doc_element)
            
            await db.commit()
            
            # Update status
            await self._update_status(db, document_id, "analyzing", f"Analyzing {len(elements)} elements")
            
            # Step 2: Analyze elements with multi-LLM
            all_findings = []
            
            for i, element in enumerate(elements):
                logger.info(f"Analyzing element {i+1}/{len(elements)}")
                
                # Multi-LLM analysis
                system_prompt, user_prompt = get_analysis_prompt(
                    element['element_type'],
                    compliance_body,
                    str(element['content']),
                    regulations
                )
                
                async with self.semaphore:
                    llm_results = await self.llm_client.call_multi_llm(
                        models=self.llm_client.get_active_models(),  # Use configured active models
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_format="json",
                        cost_tracker=cost_tracker,
                        phase="analysis",
                    )
                
                # Extract findings from each model
                element_findings = []
                for model, result in llm_results.items():
                    if 'findings' in result:
                        for finding in result['findings']:
                            finding['model_name'] = model
                            finding['element_id'] = element['element_id']
                            element_findings.append(finding)
                
                # Apply critique system if enabled
                from app.config import get_settings
                from app.services.critique_engine import get_critique_engine
                
                settings = get_settings()
                if settings.enable_critique_system and element_findings:
                    logger.info(f"Critiquing {len(element_findings)} findings from element {i+1}")
                    critique_engine = get_critique_engine()
                    
                    # Critique findings
                    critique_results = await critique_engine.critique_batch(
                        element_findings,
                        regulations,
                        str(element['content'])[:2000],  # Limit context size
                        cost_tracker=cost_tracker,
                    )
                    
                    # Filter and refine based on critique
                    for critique_result in critique_results:
                        if critique_result['status'] == 'discarded':
                            continue  # Skip discarded findings
                        
                        refined_finding = critique_result['refined_finding']
                        if refined_finding:
                            # Add critique trail to finding
                            refined_finding['critique_trail'] = critique_result['critique_trail']
                            all_findings.append(refined_finding)
                else:
                    # No critique - add findings as-is
                    all_findings.extend(element_findings)

            
            # Step 3: Build consensus  
            await self._update_status(db, document_id, "consensus", "Building consensus from multi-LLM analysis")
            
            consensus_engine = await get_consensus_engine()
            
            # Group findings by model for consensus
            llm_outputs = {}
            for finding in all_findings:
                model = finding['model_name']
                if model not in llm_outputs:
                    llm_outputs[model] = []
                llm_outputs[model].append(finding)
            
            clusters, high_confidence, medium_confidence = await consensus_engine.build_consensus(
                llm_outputs,
                element_content=extracted_data.get('full_text', ''),
                regulation_texts=[regulations]
            )
            
            logger.info(f"Consensus: {len(high_confidence)} high confidence, {len(medium_confidence)} medium")
            
            # Step 4: Dual redrafting (only if any findings)
            redraft_content = None
            all_valid_findings = high_confidence + medium_confidence
            
            if all_valid_findings:
                await self._update_status(db, document_id, "redrafting", "Generating improved document")
                redraft_content = await self._dual_redraft(
                    all_valid_findings, 
                    regulations,
                    extracted_data.get('full_text', ''),
                    cost_tracker=cost_tracker,
                )
            
            # Step 5: Generate report
            await self._update_status(db, document_id, "reporting", "Generating compliance report")
            report_content = await self._generate_report(
                high_confidence, 
                medium_confidence,
                f"Document: {document.filename or 'Unknown'}",
                cost_tracker=cost_tracker,
            )
            
            # Build cost summary
            cost_summary = cost_tracker.get_summary() if cost_tracker else {}
            
            # Update document with results including full findings and cost tracking
            await db.execute(
                update(UploadedDocument)
                .where(UploadedDocument.id == document_id)
                .values(
                    status="completed",
                    completed_at=datetime.utcnow(),
                    meta={
                        "high_confidence_count": len(high_confidence),
                        "medium_confidence_count": len(medium_confidence),
                        "total_elements": len(elements),
                        "high_confidence_findings": high_confidence,
                        "medium_confidence_findings": medium_confidence,
                        "redraft_content": redraft_content or "",
                        "report_content": report_content or "",
                        "source_text": extracted_data.get('full_text', ''),
                        "cost_tracking": cost_summary,
                    }
                )
            )
            await db.commit()
            
            logger.info(
                f"Analysis complete for document {document_id}",
                extra={"cost_summary": cost_summary},
            )
            
            return cost_tracker
            
        except Exception as e:
            logger.error(f"Error analyzing document {document_id}: {e}", exc_info=True)
            await self._update_status(db, document_id, "failed", f"Error: {str(e)}")
            raise
        finally:
            # Clean up temporary uploaded file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to remove temporary file {file_path}: {cleanup_error}")
    
    async def _retrieve_regulations(
        self,
        db: AsyncSession,
        compliance_body: str,
        compliance_section: Optional[str],
        query_text: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Retrieve relevant regulations using vector similarity search
        
        Args:
            db: Database session
            compliance_body: Name of compliance body (CARF, MHRS, DBH)
            compliance_section: Optional section filter
            query_text: Optional text for semantic search (if None, returns all top sections)
            top_k: Number of regulations to retrieve
            
        Returns:
            Concatenated regulation texts
        """
        try:
            # Get the compliance body
            result = await db.execute(
                select(ComplianceBody).where(ComplianceBody.name == compliance_body.upper())
            )
            compliance_body_obj = result.scalar_one_or_none()
            
            if not compliance_body_obj:
                logger.warning(f"Compliance body {compliance_body} not found")
                return ""
            
            # Get regulation document for this compliance body
            result = await db.execute(
                select(RegulationDocument)
                .where(RegulationDocument.compliance_body_id == compliance_body_obj.id)
                .where(RegulationDocument.status == "completed")
                .order_by(RegulationDocument.created_at.desc())
                .limit(1)
            )
            regulation_doc = result.scalar_one_or_none()
            
            if not regulation_doc:
                logger.warning(f"No completed regulation document found for {compliance_body}")
                return ""
            
            # Build query for regulation texts
            query = select(RegulationText).where(
                RegulationText.regulation_id == regulation_doc.id
            )
            
            # Apply section filter if provided
            if compliance_section:
                # Filter by section reference pattern
                query = query.where(
                    RegulationText.section_ref.ilike(f"%{compliance_section}%")
                )
            
            # If query text provided, use vector similarity search
            if query_text and query_text.strip():
                embedding_service = get_embedding_service()
                query_embedding = await embedding_service.generate_embedding(
                    query_text,
                    task_type="RETRIEVAL_QUERY"
                )
                
                # Use pgvector cosine distance for similarity
                # Order by distance (ascending = most similar first)
                query = query.order_by(
                    RegulationText.embedding_v2.cosine_distance(query_embedding)
                ).limit(top_k)
            else:
                # No query text, just get first N regulations
                query = query.limit(top_k)
            
            result = await db.execute(query)
            regulation_texts = result.scalars().all()
            
            # Fallback: If semantic search returned nothing but texts exist, get first few
            if not regulation_texts and query_text:
                logger.info(f"Fuzzy search returned no results for {compliance_body}, falling back to top regulations.")
                fallback_query = select(RegulationText).where(
                    RegulationText.regulation_id == regulation_doc.id
                ).limit(top_k)
                result = await db.execute(fallback_query)
                regulation_texts = result.scalars().all()

            if not regulation_texts:
                logger.warning(f"No regulation texts found for {compliance_body} (ID: {regulation_doc.id})")
                return ""
            
            # Format regulations for LLM context
            formatted_regs = []
            for reg in regulation_texts:
                clean_text = reg.text.strip()
                formatted_regs.append(
                    f"### SECTION {reg.section_ref}\n{clean_text}"
                )
            
            regulations_str = "\n\n---\n\n".join(formatted_regs)
            logger.info(f"Retrieved {len(regulation_texts)} regulations for {compliance_body}, total {len(regulations_str)} chars")
            
            return regulations_str
            
        except Exception as e:
            logger.error(f"Error retrieving regulations: {e}", exc_info=True)
            return ""
    
    async def _dual_redraft(self, findings: list, regulations: str, original_text: str, cost_tracker: Optional[CostTracker] = None) -> str:
        """Generate dual redrafts and select winner"""
        prompt = REDRAFT_PROMPT.format(
            original_content=original_text or "[Original document content]",
            findings=str(findings),
            regulations=regulations
        )
        
        # Determine available models for redrafting
        # Use models that are actually verified in the client
        available = self.llm_client.get_available_models()
        target_models = [m for m in ["gemini-flash", "llama-scout", "gpt-oss"] if m in available]
        
        if not target_models:
             # Fallback to any available models, prioritising larger ones if possible
             target_models = available[:2]
             
        if not target_models:
            logger.error("No models available for redrafting.")
            return ""

        redrafts = await self.llm_client.call_multi_llm(
            models=target_models,
            system_prompt="You are a compliance document editor.",
            user_prompt=prompt,
            response_format="text",
            cost_tracker=cost_tracker,
            phase="redraft",
        )
        
        # Handle overall timeout or error
        if "error" in redrafts:
            logger.error(f"Redrafting failed: {redrafts['error']}")
            return ""
        
        # Quality scoring
        scores = {}
        for model, redraft in redrafts.items():
                if not isinstance(redraft, dict) or "error" in redraft:
                    logger.warning(f"Skipping scoring for {model} due to error or invalid response.")
                    continue
                    
                # Use an available evaluator (Gemini Flash is preferred for speed/cost)
                evaluator_model = "gemini-flash" if "gemini-flash" in available else (target_models[0] if target_models else None)
                if not evaluator_model:
                     continue

                # Define the score prompt for the evaluator
                score_prompt = QUALITY_SCORE_PROMPT.format(
                    redraft_content=redraft.get('response', ""),
                    findings=str(findings)
                )

                try:
                    score_result = await self.llm_client.call_llm(
                        evaluator_model,
                        "You are a document quality evaluator.",
                        score_prompt,
                        "json",
                        cost_tracker=cost_tracker,
                        phase="redraft",
                    )
                    scores[model] = score_result.get('overall_score', 0)
                except Exception as e:
                    logger.warning(f"Scoring failed for {model} with {evaluator_model}: {e}")
                    scores[model] = 0
        
        # Select winner
        if not scores:
            # If no scores succeeded, try to find any valid redraft
            for model, redraft in redrafts.items():
                if isinstance(redraft, dict) and "response" in redraft and redraft["response"]:
                    return redraft["response"]
            return ""
            
        winner = max(scores, key=scores.get)
        return redrafts.get(winner, {}).get('response', "")
    
    async def _generate_report(self, high_conf: list, medium_conf: list, context: str, cost_tracker: Optional[CostTracker] = None) -> str:
        """Generate two-part compliance report"""
        # Combine findings for a comprehensive report
        all_findings = high_conf + medium_conf
        prompt = REPORT_SYNTHESIS_PROMPT.format(
            findings_json=str(all_findings),
            document_context=context or "[Document metadata]"
        )
        
        # Get available model for report
        report_model = "gemini-flash" if "gemini-flash" in self.llm_client.get_available_models() else (self.llm_client.get_available_models()[0] if self.llm_client.get_available_models() else None)
        
        if not report_model:
            return ""

        report = await self.llm_client.call_llm(
            report_model,
            "You are a compliance report writer.",
            prompt,
            "text",
            cost_tracker=cost_tracker,
            phase="report",
        )
        
        return report.get('response', "")
    
    async def _update_status(self, db: AsyncSession, doc_id: UUID, status: str, step: str):
        """Update document status"""
        await db.execute(
            update(UploadedDocument)
            .where(UploadedDocument.id == doc_id)
            .values(status=status)
        )
        await db.commit()
        logger.info(f"Document {doc_id}: {step}")
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
        }
        return mime_types.get(ext, 'application/pdf')
