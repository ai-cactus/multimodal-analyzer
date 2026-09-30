# Phase 1 Quick Start Guide

This guide will get you up and running with Phase 1 in under 10 minutes.

## Prerequisites Check

Run the verification script:

```bash
chmod +x scripts/verify_setup.sh
./scripts/verify_setup.sh
```

## Quick Setup (If all prerequisites met)

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your GCP credentials
nano .env
```

Required settings:

- `GCP_PROJECT_ID`: Your GCP project ID
- `DOCAI_LAYOUT_PROCESSOR_ID`: Document AI layout processor ID
- `DOCAI_FORM_PROCESSOR_ID`: Document AI form processor ID

### 2. Start Services

```bash
# Start PostgreSQL and Redis
docker compose up -d

# Check they're running
docker compose ps
```

### 3. Setup Database

```bash
# Enable pgvector extension
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Install Python dependencies
pip install -r requirements.txt

# Generate initial migration
alembic revision --autogenerate -m "Initial schema with pgvector"

# Apply migration
alembic upgrade head

# Seed compliance bodies
python scripts/seed_compliance_bodies.py
```

### 4. Start Application

```bash
# Start FastAPI application
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs to see the API documentation.

## Test the API

### Upload a Regulation Manual

```bash
curl -X POST "http://localhost:8000/api/regulations/upload" \
  -F "file=@path/to/regulation.pdf" \
  -F "compliance_body=CARF" \
  -F "version=2025" \
  -F "effective_date=2025-01-01"
```

Response:

```json
{
  "regulation_id": "uuid-here",
  "compliance_body": "CARF",
  "status": "processing",
  "total_pages": null,
  "estimated_completion": "2026-01-27T04:00:00Z"
}
```

### Check Status

```bash
curl "http://localhost:8000/api/regulations/{regulation_id}/status"
```

## GCP Processor Setup (If needed)

If you don't have Document AI processors yet:

```bash
# Enable APIs
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Create processors
gcloud documentai processors create \
  --location=us \
  --display-name="Layout Parser" \
  --type=LAYOUT_PARSER_PROCESSOR

gcloud documentai processors create \
  --location=us \
  --display-name="Form Parser" \
  --type=FORM_PARSER_PROCESSOR

# List to get IDs
gcloud documentai processors list --location=us
```

Add the processor IDs to your `.env` file.

## Troubleshooting

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker compose ps

# Check logs
docker compose logs postgres
```

### GCP Authentication Error

```bash
# Login to GCP
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## What's Working in Phase 1

✅ Regulation manual upload
✅ Document AI extraction
✅ Section parsing (CARF, MHRS, DBH)
✅ Embedding generation
✅ Vector storage in PostgreSQL
✅ Async processing
✅ Status tracking

## What's Coming in Phase 2+

⏳ Document analysis endpoints
⏳ Multi-LLM consensus
⏳ Confidence scoring
⏳ Report generation
⏳ Color-coded redrafts

## Need Help?

Check the full README.md for detailed documentation.
