"""
Pydantic schemas for regulation endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# Request Schemas
class RegulationUploadRequest(BaseModel):
    """Request schema for regulation upload"""
    compliance_body: str = Field(..., description="CARF, MHRS, or DBH")
    version: str = Field(..., description="Version year, e.g., '2025'")
    effective_date: Optional[date] = Field(None, description="Effective date of the regulation")


# Response Schemas
class RegulationUploadResponse(BaseModel):
    """Response schema for regulation upload"""
    regulation_id: UUID
    compliance_body: str
    status: str
    total_pages: Optional[int] = None
    estimated_completion: datetime
    
    class Config:
        from_attributes = True


class RegulationStatusResponse(BaseModel):
    """Response schema for regulation processing status"""
    regulation_id: UUID
    status: str
    compliance_body: str
    version: str
    total_pages: Optional[int] = None
    chunks_processed: Optional[int] = None
    total_chunks: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RegulationTextResponse(BaseModel):
    """Response schema for individual regulation text chunk"""
    id: UUID
    section_ref: str
    text: str
    page_number: Optional[int] = None
    
    class Config:
        from_attributes = True
