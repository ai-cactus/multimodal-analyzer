# Multi-LLM RAG Analysis Service

High-Performance Multi-LLM Agentic RAG Analysis for Compliance Documents

## Overview

This service provides AI-powered compliance analysis using:

- **Multi-LLM Consensus**: Gemini 2.5 Pro, Claude Opus 4.5, and Llama 4
- **Structure-Preserving Extraction**: GCP Document AI with coordinate tracking
- **High Confidence Scoring**: ≥0.90 threshold with multi-dimensional scoring
- **Agentic Processing**: LangGraph orchestration with specialized agents

## Current Status

**Phase 1: Infrastructure & Extraction** ✅

- FastAPI application with async SQLAlchemy 2.0
- PostgreSQL with pgvector for embeddings
- GCP Document AI integration
- Vertex AI embedding service
- Multi-standard section parser (CARF, MHRS, DBH)
- Regulation ingestion workflow

## Prerequisites

- Python 3.10+
- PostgreSQL 16 with pgvector extension
- Redis 7+
- GCP Project with:
  - Document AI API enabled
  - Vertex AI API enabled
  - Service account credentials
- Docker and Docker Compose (for local development)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:

- `GCP_PROJECT_ID`: Your GCP project ID
- `DOCAI_LAYOUT_PROCESSOR_ID`: Document AI layout processor ID
- `DOCAI_FORM_PROCESSOR_ID`: Document AI form processor ID
- `DATABASE_URL`: PostgreSQL connection string

### 3. Start Database Services

```bash
# Start PostgreSQL and Redis with Docker Compose
docker compose up -d

# Verify services are running
docker compose ps
```

### 4. Enable pgvector Extension

```bash
# Connect to PostgreSQL
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Exit
\q
```

### 5. Run Database Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema with pgvector"

# Apply migrations
alembic upgrade head
```

### 6. Seed Compliance Bodies

```bash
# Run seed script to create CARF, MHRS, DBH records
python scripts/seed_compliance_bodies.py
```

### 7. Start the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Or using the main module
python -m app.main
```

The API will be available at:

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## GCP Setup

### Document AI Processors

If you don't have Document AI processors yet:

```bash
# Enable Document AI API
gcloud services enable documentai.googleapis.com

# Create Layout Parser processor
gcloud documentai processors create \
  --location=us \
  --display-name="Layout Parser" \
  --type=LAYOUT_PARSER_PROCESSOR

# Create Form Parser processor
gcloud documentai processors create \
  --location=us \
  --display-name="Form Parser" \
  --type=FORM_PARSER_PROCESSOR

# List processors to get IDs
gcloud documentai processors list --location=us
```

Add the processor IDs to your `.env` file.

### Vertex AI

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

No additional setup needed for embeddings.

## API Endpoints

### Phase 1 Endpoints (Available Now)

#### POST /api/regulations/upload

Upload a compliance manual for processing.

**Form Data:**

- `file`: (file) Regulation document (PDF, DOCX)
- `compliance_body`: (string) "CARF", "MHRS", or "DBH"
- `version`: (string) Version year, e.g., "2025"
- `effective_date`: (string, optional) Effective date (YYYY-MM-DD)

curl -X 'POST' \
  'http://localhost:8000/api/regulations/upload' \
  -H 'accept: application/json' \
  -F 'file=@2025_BH_SM.pdf' \
  -F 'compliance_body=CARF' \
  -F 'version=2025'

**Response:**

```json
{
  "regulation_id": "uuid",
  "compliance_body": "CARF",
  "status": "processing",
  "total_pages": null,
  "estimated_completion": "2026-01-27T04:00:00Z"
}
```

#### GET /api/regulations/{regulation_id}/status

Check regulation processing status.

**Response:**

```json
{
  "regulation_id": "uuid",
  "status": "completed",
  "compliance_body": "CARF",
  "version": "2025",
  "total_pages": 450,
  "chunks_processed": 425,
  "total_chunks": 425,
  "created_at": "2026-01-27T03:30:00Z",
  "completed_at": "2026-01-27T03:45:00Z"
}
```

### Future Endpoints (Phase 2+)

- `POST /api/documents/analyze`: Submit document for analysis

curl -X 'POST' \
  'http://localhost:8000/api/documents/analyze' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@FOCS RISK MANAGEMENT POLICY 23.docx' \
  -F 'compliance_body=CARF' \
  -F 'output_formats=docx,pdf,json'


- `GET /api/documents/{id}/status`: Check analysis status
- `GET /api/documents/{id}/result`: Get analysis results (JSON)

curl 'http://localhost:8000/api/documents/<document_id>/result' | jq

- `GET /api/documents/{id}/report`: Download compliance report (PDF/DOCX)
- `GET /api/documents/{id}/redraft`: Get color-coded redraft

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

## Project Structure

```
multimodal-analyzer/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── api/                    # API routes
│   ├── services/               # Business logic
│   └── utils/                  # Utilities
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── docker-compose.yml          # Local services
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development Workflow

1. Make changes to code
2. Generate migration if models changed: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Test changes: `pytest`
5. Run application: `uvicorn app.main:app --reload`

## Next Steps (Phase 2-7)

- [ ] Phase 2: LangGraph Orchestration
- [ ] Phase 3: Consensus & Scoring
- [ ] Phase 4: Synthesis & Verification
- [ ] Phase 5: Output Format Generation
- [ ] Phase 6: Complete REST API
- [ ] Phase 7: Optimization & Production

## License

Copyright © 2026 Theraptly. All rights reserved.
