"""
Compliance finding models for tracking errors across iterations.
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Float, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.base import UUIDMixin


class Finding(Base, UUIDMixin):
    """
    Individual compliance findings with unique tracking IDs
    """
    __tablename__ = "findings"
    
    # Unique human-readable error ID (e.g., "err-a3f2b1")
    finding_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Link to document
    document_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False)
    
    # Iteration tracking
    iteration_number = Column(Integer, default=0, nullable=False)
    
    # Confidence and status
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    status = Column(String(20), default="active", nullable=False)  # active, resolved, false_positive
    
    # Finding details
    model_name = Column(String(100), nullable=False)  # Which model detected this
    error_type = Column(String(100), nullable=False)  # Type of compliance gap
    description = Column(Text, nullable=False)  # Detailed description
    regulation_ref = Column(String(255), nullable=True)  # Reference to regulation section
    
    # Element reference
    element_id = Column(String(255), nullable=True)  # Link to specific document element
    
    # Critique and refinement trail
    critique_trail = Column(JSONB, default=list, nullable=False)  # List of critique steps
    
    # Additional metadata
    meta = Column(JSONB, nullable=True)  # Additional finding metadata
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadedDocument", back_populates="findings")
    
    __table_args__ = (
        Index("idx_finding_document", "document_id"),
        Index("idx_finding_iteration", "document_id", "iteration_number"),
        Index("idx_finding_status", "status"),
        Index("idx_finding_confidence", "confidence_score"),
    )
    
    def __repr__(self):
        return f"<Finding(id={self.finding_id}, confidence={self.confidence_score}, status='{self.status}')>"
