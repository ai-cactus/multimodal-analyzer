"""
Pydantic schemas package
"""
from app.schemas.regulation import (
    RegulationUploadRequest,
    RegulationUploadResponse,
    RegulationStatusResponse,
    RegulationTextResponse
)
from app.schemas.document import (
    AnalyzeDocumentRequest,
    AnalyzeDocumentResponse,
    DocumentStatusResponse,
    DocumentResultResponse
)

__all__ = [
    "RegulationUploadRequest",
    "RegulationUploadResponse",
    "RegulationStatusResponse",
    "RegulationTextResponse",
    "AnalyzeDocumentRequest",
    "AnalyzeDocumentResponse",
    "DocumentStatusResponse",
    "DocumentResultResponse",
]
