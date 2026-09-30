"""
Regulation management API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta
from typing import Optional
import os
import uuid

from app.database import get_db
from app.models import RegulationDocument, ComplianceBody
from app.schemas.regulation import RegulationUploadResponse, RegulationStatusResponse
from app.services.regulation_processor import RegulationProcessor
from app.utils.logger import get_logger
from app.config import get_settings

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def list_regulations(db: AsyncSession = Depends(get_db)):
    """
    List all uploaded regulation documents
    """
    result = await db.execute(
        select(RegulationDocument, ComplianceBody)
        .join(ComplianceBody, RegulationDocument.compliance_body_id == ComplianceBody.id)
        .order_by(RegulationDocument.created_at.desc())
    )
    
    regulations = []
    for reg_doc, compliance_body in result.all():
        regulations.append({
            "regulation_id": str(reg_doc.id),
            "compliance_body": compliance_body.name,
            "compliance_body_full_name": compliance_body.full_name,
            "version": reg_doc.version,
            "filename": reg_doc.filename,
            "status": reg_doc.status,
            "total_pages": reg_doc.total_pages,
            "effective_date": reg_doc.effective_date.isoformat() if reg_doc.effective_date else None,
            "created_at": reg_doc.created_at.isoformat(),
            "completed_at": reg_doc.completed_at.isoformat() if reg_doc.completed_at else None
        })
    
    return {
        "total": len(regulations),
        "regulations": regulations
    }

settings = get_settings()


@router.post("/upload", response_model=RegulationUploadResponse)
async def upload_regulation(
    file: UploadFile = File(...),
    compliance_body: str = Form(..., description="CARF, MHRS, or DBH"),
    version: str = Form(..., description="Version year, e.g., '2025'"),
    effective_date: Optional[str] = Form(None, description="Effective date (YYYY-MM-DD)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a compliance regulation manual for processing
    
    This endpoint:
    1. Saves the uploaded file
    2. Creates a RegulationDocument record
    3. Queues async processing (extraction, chunking, embedding)
    4. Returns processing status
    """
    logger.info(f"Received regulation upload: {file.filename} for {compliance_body}")
    
    # Validate compliance body
    result = await db.execute(
        select(ComplianceBody).where(ComplianceBody.name == compliance_body.upper())
    )
    compliance_body_obj = result.scalar_one_or_none()
    
    if not compliance_body_obj:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid compliance body: {compliance_body}. Valid options: CARF, MHRS, DBH"
        )
    
    # Parse effective date
    parsed_effective_date = None
    if effective_date:
        try:
            parsed_effective_date = datetime.strptime(effective_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid effective_date format. Use YYYY-MM-DD"
            )
    
    # Create upload directory if not exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Save uploaded file
    regulation_id = uuid.uuid4()
    file_extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.upload_dir, f"{regulation_id}{file_extension}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"Saved regulation file to: {file_path}")
    
    # Create regulation document record
    regulation_doc = RegulationDocument(
        id=regulation_id,
        compliance_body_id=compliance_body_obj.id,
        version=version,
        effective_date=parsed_effective_date,
        filename=file.filename,
        status="processing"
    )
    
    db.add(regulation_doc)
    await db.commit()
    await db.refresh(regulation_doc)
    
    # Queue async processing
    processor = RegulationProcessor()
    background_tasks.add_task(
        processor.process_regulation,
        db=db,
        regulation_id=regulation_id,
        file_path=file_path,
        compliance_body_id=compliance_body_obj.id,
        version=version,
        effective_date=parsed_effective_date
    )
    
    logger.info(f"Queued regulation processing for {regulation_id}")
    
    # Return response
    return RegulationUploadResponse(
        regulation_id=regulation_id,
        compliance_body=compliance_body.upper(),
        status="processing",
        total_pages=None,
        estimated_completion=datetime.utcnow() + timedelta(minutes=10)
    )


@router.get("/{regulation_id}/status", response_model=RegulationStatusResponse)
async def get_regulation_status(
    regulation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status of a regulation document
    """
    result = await db.execute(
        select(RegulationDocument).where(RegulationDocument.id == regulation_id)
    )
    regulation = result.scalar_one_or_none()
    
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    # Get compliance body
    result = await db.execute(
        select(ComplianceBody).where(ComplianceBody.id == regulation.compliance_body_id)
    )
    compliance_body = result.scalar_one()
    
    # Count processed chunks
    from app.models import RegulationText
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).where(RegulationText.regulation_id == regulation_id)
    )
    chunks_count = result.scalar() or 0
    
    return RegulationStatusResponse(
        regulation_id=regulation.id,
        status=regulation.status,
        compliance_body=compliance_body.name,
        version=regulation.version,
        total_pages=regulation.total_pages,
        chunks_processed=chunks_count if regulation.status == "completed" else None,
        total_chunks=chunks_count if regulation.status == "completed" else None,
        created_at=regulation.created_at,
        completed_at=regulation.completed_at
    )
@router.post("/{regulation_id}/retry", response_model=RegulationUploadResponse)
async def retry_regulation(
    regulation_id: uuid.UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Retry processing a failed regulation document
    """
    result = await db.execute(
        select(RegulationDocument).where(RegulationDocument.id == regulation_id)
    )
    regulation = result.scalar_one_or_none()
    
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    if regulation.status == "completed":
        raise HTTPException(status_code=400, detail="Regulation already completed")
    
    # Reconstruct file path
    file_extension = os.path.splitext(regulation.filename)[1]
    file_path = os.path.join(settings.upload_dir, f"{regulation.id}{file_extension}")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=400,
            detail="Source file no longer exists. Please re-upload the regulation."
        )
    
    # Update status to processing
    regulation.status = "processing"
    await db.commit()
    
    # Re-queue async processing
    processor = RegulationProcessor()
    background_tasks.add_task(
        processor.process_regulation,
        db=db,
        regulation_id=regulation.id,
        file_path=file_path,
        compliance_body_id=regulation.compliance_body_id,
        version=regulation.version,
        effective_date=regulation.effective_date
    )
    
    logger.info(f"Retrying regulation processing for {regulation_id}")
    
    # Get compliance body name
    result = await db.execute(
        select(ComplianceBody).where(ComplianceBody.id == regulation.compliance_body_id)
    )
    compliance_body = result.scalar_one()
    
    return RegulationUploadResponse(
        regulation_id=regulation.id,
        compliance_body=compliance_body.name,
        status="processing",
        total_pages=regulation.total_pages,
        estimated_completion=datetime.utcnow() + timedelta(minutes=10)
    )


@router.delete("/{regulation_id}")
async def delete_regulation(
    regulation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a regulation document and all its text chunks
    """
    from sqlalchemy import delete
    from app.models import RegulationText
    
    # Check if exists
    result = await db.execute(
        select(RegulationDocument).where(RegulationDocument.id == regulation_id)
    )
    regulation = result.scalar_one_or_none()
    
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
        
    try:
        # Delete text chunks first
        await db.execute(
            delete(RegulationText).where(RegulationText.regulation_id == regulation_id)
        )
        
        # Delete document record
        await db.execute(
            delete(RegulationDocument).where(RegulationDocument.id == regulation_id)
        )
        
        await db.commit()
        
        # Delete file if exists
        file_extension = os.path.splitext(regulation.filename)[1]
        file_path = os.path.join(settings.upload_dir, f"{regulation.id}{file_extension}")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            
        return {"message": f"Successfully deleted regulation {regulation_id}"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting regulation {regulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

