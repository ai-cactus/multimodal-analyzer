"""
User document and element models
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.base import UUIDMixin, generate_uuid


class UploadedDocument(Base, UUIDMixin):
    """
    Documents uploaded for compliance analysis
    """
    __tablename__ = "uploaded_documents"
    
    filename = Column(String(255), nullable=False)
    compliance_body_id = Column(Integer, ForeignKey("compliance_bodies.id"), nullable=False)
    compliance_section = Column(String(100), nullable=True)  # Optional section filter (e.g., "§3409-3412")
    status = Column(String(50), default="processing", nullable=False)  # processing, completed, failed
    total_pages = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)  # Temporary storage path
    redraft_mode = Column(String(50), default="color_coded", nullable=False)  # color_coded, clean, both
    output_formats = Column(JSONB, default=["docx"], nullable=False)  # ["docx", "html", "pdf"]
    
    # Iteration tracking for automatic refinement
    iteration_count = Column(Integer, default=0, nullable=False)  # Current iteration number
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_documents.id"), nullable=True)  # Link to original document
    iteration_history = Column(JSONB, default=list, nullable=False)  # Metadata for each iteration
    
    meta = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    compliance_body = relationship("ComplianceBody", back_populates="documents")
    elements = relationship("DocumentElement", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_document_status", "status"),
    )
    
    def __repr__(self):
        return f"<UploadedDocument(id={self.id}, filename='{self.filename}')>"


class DocumentElement(Base, UUIDMixin):
    """
    Extracted document elements with structure preservation
    """
    __tablename__ = "document_elements"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False)
    element_type = Column(String(50), nullable=False)  # text, table, form, list_item, numbering
    parent_id = Column(UUID(as_uuid=True), ForeignKey("document_elements.id"), nullable=True)
    page_number = Column(Integer, nullable=False)
    section_path = Column(Text, nullable=True)  # e.g., "Section 3 > Table 1"
    order_index = Column(Integer, nullable=False)
    bounding_box = Column(JSONB, nullable=True)  # Coordinates from Document AI
    content = Column(JSONB, nullable=False)  # Structured content
    raw_docai_output = Column(JSONB, nullable=True)  # Full Document AI response for this element
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadedDocument", back_populates="elements")
    
    __table_args__ = (
        Index("idx_doc_hierarchy", "document_id", "parent_id"),
        Index("idx_doc_order", "document_id", "page_number", "order_index"),
    )
    
    def __repr__(self):
        return f"<DocumentElement(id={self.id}, type='{self.element_type}', page={self.page_number})>"
