# FastAPI Migration Guide

This project uses **FastAPI** instead of Django for superior async performance and native Pydantic integration.

## Key FastAPI Implementation Examples

### 1. Main Application Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="RAG Analysis Service API",
    description="High-Performance Multi-LLM Agentic RAG Analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.routes import regulations, documents
app.include_router(regulations.router, prefix="/api/regulations", tags=["regulations"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### 2. Async Database Session (SQLAlchemy 2.0)

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_maker() as session:
        yield session
```

### 3. FastAPI Endpoint with File Upload

```python
#routes/documents.py
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analysis import process_document_async
import uuid

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(...),
    compliance_body_id: int = Form(...),
    compliance_section: str | None = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """Submit a document for compliance analysis"""

    document_id = uuid.uuid4()

    # Save file
    file_path = f"/tmp/{document_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Queue async processing
    background_tasks.add_task(
        process_document_async,
        document_id=document_id,
        file_path=file_path,
        compliance_body_id=compliance_body_id,
        compliance_section=compliance_section,
        db=db
    )

    return AnalyzeResponse(
        document_id=str(document_id),
        status="processing",
        estimated_completion="2026-01-27T03:30:00Z",
        check_url=f"/api/documents/{document_id}/status"
    )
```

### 4. Pydantic Schemas (Request/Response)

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AnalyzeRequest(BaseModel):
    compliance_body_id: int
    compliance_section: Optional[str] = None
    filename: str
    redraft_mode: str = Field(default="color_coded", pattern="^(color_coded|clean|both)$")
    output_formats: List[str] = Field(default=["docx"])

class AnalyzeResponse(BaseModel):
    document_id: str
    status: str
    estimated_completion: datetime
    check_url: str

class Finding(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: Literal["gap", "inconsistency", "non-compliance", "structural"]
    severity: Literal["critical", "major", "minor"]
    description: str
    evidence: str
    regulation_ref: str
```

### 5. Async Query with SQLAlchemy 2.0

```python
# services/regulations.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import RegulationText
from pgvector.sqlalchemy import CosineDistance

async def retrieve_relevant_regulations(
    policy_text: str,
    compliance_body_id: int,
    compliance_section: Optional[str],
    db: AsyncSession
) -> List[RegulationText]:
    """Async vector similarity search"""

    # Generate embedding
    policy_embedding = await vertex_embedding_service.generate_embedding(
        policy_text,
        task_type="RETRIEVAL_QUERY"
    )

    # Build query
    stmt = select(RegulationText).where(
        RegulationText.regulation.has(compliance_body_id=compliance_body_id)
    )

    if compliance_section:
        section_pattern = parse_section_range(compliance_section)
        stmt = stmt.where(RegulationText.section_ref.regexp_match(section_pattern))

    # Vector similarity search
    stmt = stmt.order_by(
        CosineDistance(RegulationText.embedding_v2, policy_embedding)
    ).limit(5)

    result = await db.execute(stmt)
    return result.scalars().all()
```

## Database Migrations (Alembic)

### Setup

```bash
# Install alembic
pip install alembic

# Initialize alembic
alembic init alembic

# Edit alembic.ini
sqlalchemy.url = postgresql+asyncpg://user:password@localhost/dbname
```

### Create Migration

```bash
# Auto-generate migration from models
alembic revision --autogenerate -m "initial schema"

# Apply migration
alembic upgrade head
```

### Migration File Example

```python
# alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

def upgrade():
    op.create_table(
        'document_elements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('element_type', sa.String(50), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('page_number', sa.Integer()),
        sa.Column('section_path', sa.Text()),
        sa.Column('order_index', sa.Integer()),
        sa.Column('bounding_box', postgresql.JSONB()),
        sa.Column('content', postgresql.JSONB()),
        sa.Column('raw_docai_output', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP()),
        sa.ForeignKeyConstraint(['document_id'], ['uploaded_documents.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['document_elements.id'])
    )

    op.create_index('idx_doc_hierarchy', 'document_elements', ['document_id', 'parent_id'])
    op.create_index('idx_doc_order', 'document_elements', ['document_id', 'page_number', 'order_index'])

    op.create_table(
        'regulation_texts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_ref', sa.Text()),
        sa.Column('text', sa.Text()),
        sa.Column('embedding_v2', Vector(768)),
        sa.Column('created_at', sa.TIMESTAMP()),
        sa.ForeignKeyConstraint(['regulation_id'], ['regulation_documents.id'])
    )

def downgrade():
    op.drop_table('regulation_texts')
    op.drop_table('document_elements')
```

## Key Advantages Over Django

1. **Native Async**: All database queries and LLM calls run concurrently
2. **Auto Docs**: Swagger UI at `/docs`, ReDoc at `/redoc`
3. **Type Safety**: Pydantic validation catches errors at request time
4. **Performance**: 5-10x faster for I/O-bound workloads
5. **Modern**: Built for Python 3.10+ type hints

## Running the Application

```bash
# Development
uvicorn main:app --reload --port 8000

# Production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
