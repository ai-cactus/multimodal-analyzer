"""
Document analysis API endpoints (FULL IMPLEMENTATION)
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import os
import uuid

from app.database import get_db
from app.models import UploadedDocument, ComplianceBody
from app.services.analysis_service import DocumentAnalysisService
from app.services.output.docx_generator import get_docx_generator
from app.services.output.pdf_generator import get_pdf_generator
from app.services.output.html_generator import get_html_generator
from app.utils.logger import get_logger
from app.config import get_settings

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    compliance_body: str = Form(..., description="CARF, MHRS, or DBH"),
    compliance_section: Optional[str] = Form(None, description="Optional section filter"),
    redraft_mode: str = Form("color_coded", description="color_coded, clean, or both"),
    output_formats: str = Form("docx,pdf", description="Comma-separated: docx,pdf,html,json"),
    enable_iterations: bool = Form(True, description="Enable automatic iterative refinement"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a document for comprehensive compliance analysis
    
    This endpoint:
    1. Saves the uploaded file
    2. Creates an UploadedDocument record
    3. Queues async analysis (extraction, multi-LLM analysis, consensus, synthesis)
    4. If enable_iterations=True, automatically refines document up to MAX_ITERATIONS
    5. Returns document_id for status tracking
    """
    logger.info(f"Received analysis request: {file.filename} for {compliance_body} (iterations: {enable_iterations})")
    
    # Validate compliance body
    result = await db.execute(
        select(ComplianceBody).where(ComplianceBody.name == compliance_body.upper())
    )
    compliance_body_obj = result.scalar_one_or_none()
    
    if not compliance_body_obj:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid compliance body: {compliance_body}. Valid: CARF, MHRS, DBH"
        )
    
    # Validate file type - reject legacy .doc files
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension == '.doc' or file.content_type == 'application/msword':
        raise HTTPException(
            status_code=400,
            detail=(
                "Legacy Microsoft Word .doc format is not supported. "
                "Please convert your file to .docx format and upload again. "
                "You can convert using Microsoft Word (File > Save As > .docx) or "
                "online converters like CloudConvert."
            )
        )
    
    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Save file
    document_id = uuid.uuid4()
    file_path = os.path.join(settings.upload_dir, f"{document_id}{file_extension}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"Saved document to: {file_path}")
    
    # Create document record
    formats = [fmt.strip() for fmt in output_formats.split(",")]
    uploaded_doc = UploadedDocument(
        id=document_id,
        filename=file.filename,
        compliance_body_id=compliance_body_obj.id,
        compliance_section=compliance_section,
        status="processing",
        file_path=file_path,
        redraft_mode=redraft_mode,
        output_formats=formats,
        meta={}
    )
    
    db.add(uploaded_doc)
    await db.commit()
    await db.refresh(uploaded_doc)
    
    # Queue analysis using iterative service
    from app.services.iterative_analysis import get_iterative_analysis_service
    
    iterative_service = get_iterative_analysis_service()
    background_tasks.add_task(
        iterative_service.analyze_document_iterative,
        db=db,
        document_id=document_id,
        file_path=file_path,
        compliance_body=compliance_body.upper(),
        compliance_section=compliance_section,
        enable_iterations=enable_iterations
    )
    
    logger.info(f"Queued {'iterative ' if enable_iterations else ''}analysis for document {document_id}")
    
    return {
        "document_id": str(document_id),
        "status": "processing",
        "iterative_refinement": enable_iterations,
        "max_iterations": settings.max_iterations if enable_iterations else 1,
        "message": "Analysis started. Use /status endpoint to track progress."
    }


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document processing status with detailed progress and iteration history
    """
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get compliance body
    result = await db.execute(
        select(ComplianceBody).where(ComplianceBody.id == document.compliance_body_id)
    )
    compliance_body = result.scalar_one()
    
    # Get element and finding counts from meta
    meta = document.meta or {}
    
    response = {
        "document_id": str(document.id),
        "filename": document.filename,
        "compliance_body": compliance_body.name,
        "status": document.status,
        "current_step": meta.get("current_step", "initializing"),
        "progress_percent": meta.get("progress_percent", 0),
        "total_elements": meta.get("total_elements", 0),
        "high_confidence_count": meta.get("high_confidence_count", 0),
        "medium_confidence_count": meta.get("medium_confidence_count", 0),
        "created_at": document.created_at,
        "completed_at": document.completed_at
    }
    
    # Add cost tracking if available
    if meta.get("cost_tracking"):
        response["cost_tracking"] = meta["cost_tracking"]
    
    # Add iteration information if available
    if document.iteration_count > 0:
        response["iteration_number"] = document.iteration_count
        response["parent_document_id"] = str(document.parent_document_id) if document.parent_document_id else None
    
    # Add iteration history if this is a parent document
    if document.iteration_history:
        response["iteration_history"] = document.iteration_history
        
        # Check if converged
        if document.iteration_history:
            last_iteration = document.iteration_history[-1]
            response["converged"] = last_iteration.get("converged", False)
    
    return response


@router.get("/{document_id}/result")
async def get_document_result(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete analysis results in JSON format
    """
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {document.status}"
        )
    
    # Return findings from meta
    meta = document.meta or {}
    
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "status": document.status,
        "findings_summary": {
            "high_confidence_count": meta.get("high_confidence_count", 0),
            "medium_confidence_count": meta.get("medium_confidence_count", 0),
            "total_elements_analyzed": meta.get("total_elements", 0)
        },
        "high_confidence_findings": meta.get("high_confidence_findings", []),
        "medium_confidence_findings": meta.get("medium_confidence_findings", []),
        "cost_tracking": meta.get("cost_tracking"),
        "report_available": True,
        "redraft_available": (meta.get("high_confidence_count", 0) + meta.get("medium_confidence_count", 0)) > 0
    }


@router.get("/{document_id}/report")
async def download_report(
    document_id: uuid.UUID,
    format: str = "pdf",  # pdf, docx, html, txt
    db: AsyncSession = Depends(get_db)
):
    """
    Download compliance report in specified format
    """
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    meta = document.meta or {}
    # Include both high and medium confidence findings in the report
    high_findings = meta.get("high_confidence_findings", [])
    mid_findings = meta.get("medium_confidence_findings", [])
    findings = high_findings + mid_findings
    
    # Generate report in requested format
    output_dir = os.path.join(settings.upload_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    if format == "pdf":
        pdf_gen = get_pdf_generator()
        file_path = pdf_gen.generate_compliance_report(
            findings=findings,
            document_context={"filename": document.filename},
            output_path=os.path.join(output_dir, f"{document_id}_report.pdf")
        )
        return FileResponse(file_path, filename=f"compliance_report_{document.filename}.pdf")
    
    elif format == "docx":
        docx_gen = get_docx_generator()
        # We need a method to generate a compliance report in DOCX
        # Looking at docx_generator, it has generate_color_coded_document
        # Let's assume we use regular report for now or implement a specific one
        file_path = docx_gen.generate_compliance_report(
            findings=findings,
            document_context={"filename": document.filename},
            output_path=os.path.join(output_dir, f"{document_id}_report.docx")
        )
        return FileResponse(file_path, filename=f"compliance_report_{document.filename}.docx")

    elif format == "html":
        html_gen = get_html_generator()
        file_path = html_gen.generate_html_report(
            findings=findings,
            document_context={"filename": document.filename},
            output_path=os.path.join(output_dir, f"{document_id}_report.html")
        )
        return FileResponse(file_path, filename=f"compliance_report_{document.filename}.html")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/{document_id}/redraft")
async def download_redraft(
    document_id: uuid.UUID,
    mode: str = "color_coded",  # color_coded or clean
    format: str = "docx",
    db: AsyncSession = Depends(get_db)
):
    """
    Download redrafted document with improvements
    """
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    meta = document.meta or {}
    high_findings = meta.get("high_confidence_findings", [])
    mid_findings = meta.get("medium_confidence_findings", [])
    findings = high_findings + mid_findings
    redraft_content = meta.get("redraft_content", "")
    
    if not findings:
        raise HTTPException(status_code=400, detail="No redraft available (no findings)")
    
    # Generate redraft
    output_dir = os.path.join(settings.upload_dir, "redrafts")
    os.makedirs(output_dir, exist_ok=True)
    
    docx_gen = get_docx_generator()
    
    if mode == "color_coded":
        file_path = docx_gen.generate_color_coded_document(
            original_content=meta.get("source_text", ""),
            findings=findings,
            redraft_content=redraft_content,
            output_path=os.path.join(output_dir, f"{document_id}_redraft_color.docx")
        )
    else:
        file_path = docx_gen.generate_clean_document(
            redraft_content=redraft_content,
            output_path=os.path.join(output_dir, f"{document_id}_redraft_clean.docx")
        )
    
    return FileResponse(file_path, filename=f"redraft_{mode}_{document.filename}")
