"""
Compliance body models
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ComplianceBody(Base):
    """
    Compliance bodies/standards: CARF, MHRS, DBH
    """
    __tablename__ = "compliance_bodies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # "CARF", "MHRS", "DBH"
    full_name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    regulations = relationship("RegulationDocument", back_populates="compliance_body")
    documents = relationship("UploadedDocument", back_populates="compliance_body")
    
    def __repr__(self):
        return f"<ComplianceBody(id={self.id}, name='{self.name}')>"
