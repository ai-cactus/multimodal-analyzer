"""
Regulation document and text models
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Index, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.database import Base
from app.models.base import UUIDMixin, generate_uuid


class RegulationDocument(Base, UUIDMixin):
    """
    Uploaded regulation manuals (CARF, MHRS, DBH standards)
    """
    __tablename__ = "regulation_documents"
    
    compliance_body_id = Column(Integer, ForeignKey("compliance_bodies.id"), nullable=False)
    version = Column(String(50), nullable=False)  # e.g., "2025"
    effective_date = Column(Date, nullable=True)
    filename = Column(String(255), nullable=False)
    total_pages = Column(Integer, nullable=True)
    status = Column(String(50), default="processing", nullable=False)  # processing, completed, failed
    meta = Column(JSONB, nullable=True)  # Additional metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    compliance_body = relationship("ComplianceBody", back_populates="regulations")
    texts = relationship("RegulationText", back_populates="regulation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_regulation_body_version", "compliance_body_id", "version"),
    )
    
    def __repr__(self):
        return f"<RegulationDocument(id={self.id}, body={self.compliance_body_id}, version='{self.version}')>"


class RegulationText(Base, UUIDMixin):
    """
    Chunked regulation text with embeddings for RAG retrieval
    """
    __tablename__ = "regulation_texts"
    
    regulation_id = Column(UUID(as_uuid=True), ForeignKey("regulation_documents.id", ondelete="CASCADE"), nullable=False)
    section_ref = Column(Text, nullable=False)  # e.g., "§3409.1", "1.B.5.a"
    text = Column(Text, nullable=False)
    embedding_v2 = Column(Vector(768), nullable=True)  # Vertex AI text-embedding-005
    page_number = Column(Integer, nullable=True)
    meta = Column(JSONB, nullable=True)  # sub_chunk info, context, etc.
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    regulation = relationship("RegulationDocument", back_populates="texts")
    
    __table_args__ = (
        Index("idx_regulation_section", "regulation_id", "section_ref"),
        Index("idx_embedding_vector", "embedding_v2", postgresql_using="ivfflat", postgresql_with={"lists": 100}),
    )
    
    def __repr__(self):
        return f"<RegulationText(id={self.id}, section='{self.section_ref}')>"
