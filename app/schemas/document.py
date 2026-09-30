"""
Pydantic schemas for document analysis endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Request Schemas
class AnalyzeDocumentRequest(BaseModel):
    """Request schema for document analysis"""
    compliance_body_id: int = Field(..., description="Compliance body ID")
    compliance_section: Optional[str] = Field(None, description="Optional section filter, e.g., '§3409-3412'")
    redraft_mode: str = Field(default="color_coded", pattern="^(color_coded|clean|both)$")
    output_formats: List[str] = Field(default=["docx"], description="Output formats: docx, html, pdf, json")


# Response Schemas
class AnalyzeDocumentResponse(BaseModel):
    """Response schema for document analysis submission"""
    document_id: UUID
    status: str
    estimated_completion: datetime
    check_url: str
    
    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    """Response schema for document processing status"""
    document_id: UUID
    status: str
    progress: dict
    estimated_completion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LLMModelCost(BaseModel):
    """Cost breakdown for a single LLM model"""
    input_tokens: int = 0
    output_tokens: int = 0
    call_count: int = 0
    cost_usd: float = 0.0


class LLMCostSummary(BaseModel):
    """Aggregated LLM cost summary"""
    total_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_calls: int = 0
    per_model: dict = Field(default_factory=dict, description="Per-model cost breakdown")


class DocAIParserCost(BaseModel):
    """Cost for a single Document AI parser"""
    pages: int = 0
    cost_usd: float = 0.0


class DocAICostSummary(BaseModel):
    """Aggregated Document AI cost summary"""
    total_usd: float = 0.0
    parsers: dict = Field(default_factory=dict, description="Per-parser cost breakdown")


class CostTrackingResponse(BaseModel):
    """Full cost tracking breakdown for a document analysis"""
    total_cost_usd: float = 0.0
    llm_costs: Optional[LLMCostSummary] = None
    docai_costs: Optional[DocAICostSummary] = None
    phase_breakdown: dict = Field(default_factory=dict, description="Cost by analysis phase")
    elapsed_seconds: float = 0.0
    document_id: Optional[str] = None


class DocumentResultResponse(BaseModel):
    """Response schema for document analysis results"""
    document_id: UUID
    status: str
    overall_compliance_score: float
    high_confidence_findings: List[dict]
    medium_confidence_findings: List[dict]
    total_findings: int
    critical_count: int
    major_count: int
    minor_count: int
    cost_tracking: Optional[CostTrackingResponse] = None
    
    class Config:
        from_attributes = True

