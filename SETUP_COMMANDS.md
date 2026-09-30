# Phase 1 Implementation - Setup Commands Summary

## Prerequisites Verification

```bash
# Run setup verification
./scripts/verify_setup.sh
```

## Step-by-Step Setup

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your GCP credentials (use nano, vim, or your preferred editor)
nano .env
```

**Required Environment Variables**:

```bash
GCP_PROJECT_ID=your-actual-project-id
DOCAI_LAYOUT_PROCESSOR_ID=your-layout-processor-id
DOCAI_FORM_PROCESSOR_ID=your-form-processor-id
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rag_analyzer
```

### 2. Start Docker Services

```bash
# Start PostgreSQL with pgvector and Redis
docker compose up -d

# Verify services are running
docker compose ps
```

### 3. Enable pgvector Extension

```bash
# Connect to PostgreSQL and enable pgvector
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 4. Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Generate initial migration from models
alembic revision --autogenerate -m "Initial schema with pgvector"

# Apply migration to create tables
alembic upgrade head
```

### 6. Seed Compliance Bodies

```bash
# Populate CARF, MHRS, DBH records
python scripts/seed_compliance_bodies.py
```

### 7. Start the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Application will be available at:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## Testing the API

### Test Regulation Upload

```bash
# Upload a regulation manual (replace path with actual file)
curl -X POST "http://localhost:8000/api/regulations/upload" \
  -F "file=@/path/to/regulation.pdf" \
  -F "compliance_body=CARF" \
  -F "version=2025" \
  -F "effective_date=2025-01-01"
```

**Expected Response**:

```json
{
  "regulation_id": "some-uuid-here",
  "compliance_body": "CARF",
  "status": "processing",
  "total_pages": null,
  "estimated_completion": "2026-01-27T04:XX:XX"
}
```

### Check Processing Status

```bash
# Replace {regulation_id} with the UUID from upload response
curl "http://localhost:8000/api/regulations/{regulation_id}/status"
```

**Expected Response** (when completed):

```json
{
  "regulation_id": "some-uuid-here",
  "status": "completed",
  "compliance_body": "CARF",
  "version": "2025",
  "total_pages": 450,
  "chunks_processed": 425,
  "total_chunks": 425,
  "created_at": "2026-01-27T...",
  "completed_at": "2026-01-27T..."
}
```

## GCP Setup (If Needed)

### If you don't have Document AI processors yet:

```bash
# Enable required APIs
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com

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

# List processors to get their IDs
gcloud documentai processors list --location=us
```

Copy the processor IDs and add them to your `.env` file.

## Troubleshooting

### Database Connection Error

```bash
# Check Docker services
docker compose ps

# View PostgreSQL logs
docker compose logs postgres

# Restart if needed
docker compose restart postgres
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or reinstall specific package
pip install --upgrade google-cloud-documentai
```

### GCP Authentication

```bash
# Authenticate with GCP
gcloud auth application-default login

# Set active project
gcloud config set project YOUR_PROJECT_ID
```

### Migration Errors

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Downgrade if needed
alembic downgrade -1

# Re-run upgrade
alembic upgrade head
```

## Useful Commands

```bash
# View application logs (if running in background)
tail -f logs/app.log

# Check database tables
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "\dt"

# Check pgvector extension
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "\dx"

# Run tests
pytest tests/

# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

## Next Steps After Setup

1. ✅ Verify all services are running
2. ✅ Test regulation upload with a sample PDF
3. ✅ Check status endpoint returns data
4. ✅ Review Swagger UI documentation
5. ⏭️ Ready for Phase 2 implementation!

## Documentation References

- [README.md](./README.md) - Full documentation
- [QUICKSTART.md](./QUICKSTART.md) - Quick start guide
- [walkthrough.md](./walkthrough.md) - Implementation details
- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) - System design
- [RAG_IMPLEMENTATION_PLAN.md](./RAG_IMPLEMENTATION_PLAN.md) - 7-phase plan

---

**Phase 1 Complete** ✅ - Infrastructure & Extraction Layer Ready!
