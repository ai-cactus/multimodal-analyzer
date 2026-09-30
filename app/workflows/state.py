"""
LangGraph state schema for RAG analysis workflow
"""
from typing import TypedDict, List, Dict, Annotated, Optional
import operator
from datetime import datetime
from uuid import UUID


class Finding(TypedDict):
    """Individual finding from an LLM"""
    claim_id: str
    element_id: str
    issue_type: str  # gap, inconsistency, non-compliance, structural
    severity: str  # critical, major, minor
    description: str
    evidence: str
    regulation_ref: str
    model_name: str  # gemini, claude, llama
    confidence: Optional[float]


class ClaimCluster(TypedDict):
    """Cluster of semantically similar findings"""
    cluster_id: str
    findings: List[Finding]
    representative_finding: Finding
    model_agreement: float  # 0.0 to 1.0
    confidence_score: float  # Multi-dimensional score
    is_high_confidence: bool  # >= 0.90


class RedraftCandidate(TypedDict):
    """Redrafted content from a model"""
    model_name: str
    content: str
    quality_score: float


class RAGAnalysisState(TypedDict):
    """
    State for the RAG analysis workflow
    Tracks document processing through extraction, analysis, consensus, and synthesis
    """
    
    # Document metadata
    document_id: UUID
    filename: str
    compliance_body: str
    compliance_section: Optional[str]
    
    # Extraction results
    elements: List[Dict]  # Extracted document elements
    current_element_idx: int  # Current element being processed
    total_elements: int
    
    # Retrieved regulations
    retrieved_regulations: List[Dict]
    
    # Multi-LLM analysis outputs (additive)
    llm_outputs: Annotated[Dict[str, List[Finding]], operator.add]
    
    # Consensus results
    claim_clusters: List[ClaimCluster]
    high_confidence_findings: List[Finding]  # score >= 0.90
    medium_confidence_findings: List[Finding]  # 0.70 <= score < 0.90
    
    # Synthesis
    redraft_candidates: Dict[str, RedraftCandidate]  # {model_name: candidate}
    selected_redraft: str
    final_report: str
    
    # Verification
    verification_scores: Dict[str, float]  # {model_name: score}
    final_confidence: float
    verification_passed: bool
    
    # Status tracking
    status: str  # extracting, analyzing, consensus, redrafting, verifying, complete
    current_step: str
    progress_percent: float
    started_at: datetime
    completed_at: Optional[datetime]
    
    # Errors (additive)
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]


class AnalysisProgress(TypedDict):
    """Progress tracking for status endpoint"""
    current_step: str
    percent_complete: float
    elements_processed: int
    total_elements: int
    high_confidence_count: int
    medium_confidence_count: int
    estimated_completion: Optional[datetime]
