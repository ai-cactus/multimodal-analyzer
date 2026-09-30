# Quick Start Guide: Advanced Compliance Analysis System

## ✅ Implementation Status

All features from the WORK_PLAN.md have been successfully implemented:

- ✅ **Increased Confidence Thresholds** (0.95 high, 0.80 medium)
- ✅ **Recursive Error-Centric Analysis** with unique error IDs
- ✅ **Targeted Conflict Resolution** via critique system
- ✅ **Multi-LLM Critique System** (Proposer → Critic → Refiner)
- ✅ **Well-Formatted Output** (color-coded DOCX, clean DOCX, HTML)

## 🚀 Deployment Steps

### Step 1: Update Environment Variables

Add these to your `.env` file (examples in `.env.example`):

```bash
# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD=0.95
MEDIUM_CONFIDENCE_THRESHOLD=0.80

# Iterative Refinement (up to 5 iterations)
MAX_ITERATIONS=5
CONVERGENCE_THRESHOLD=0

# Multi-LLM Critique System
ENABLE_CRITIQUE_SYSTEM=true
PROPOSER_MODEL=gemini-flash
CRITIC_MODEL=llama-scout
USE_CRITIQUE_IN_SINGLE_MODEL=true

# Consensus Method
CONSENSUS_METHOD=hybrid  # hybrid, agreement, or confidence
MIN_MODEL_AGREEMENT=0.66
```

### Step 2: Run Database Migration

```bash
# Start your database (if using Docker)
docker-compose up -d postgres

# Apply the migration
cd /home/oluwaseyi/dev247/official/multimodal-analyzer
alembic upgrade head
```

Migration adds:

- `findings` table (with unique error IDs)
- `iteration_count`, `parent_document_id`, `iteration_history` columns to `uploaded_documents`

### Step 3: Restart the Application

```bash
# If using Docker
docker-compose restart app

# Or directly
uvicorn app.main:app --reload
```

## 🧪 Testing the System

### Test 1: Single Document Analysis (With Iterations)

```bash
# Submit a document for iterative analysis
curl -X POST "http://localhost:8000/api/documents/analyze" \
  -F "file=@your_policy.docx" \
  -F "compliance_body=CARF" \
  -F "enable_iterations=true" \
  > response.json

# Extract document ID
DOCUMENT_ID=$(cat response.json | jq -r '.document_id')
echo "Document ID: $DOCUMENT_ID"

# Monitor progress (polls every 5 seconds)
watch -n 5 "curl -s http://localhost:8000/api/documents/$DOCUMENT_ID/status | jq"
```

**What to expect:**

- System analyzes the document (Iteration 0)
- If gaps found, generates redraft and re-analyzes (Iteration 1, 2, ...)
- Stops when high-confidence findings = 0 OR max iterations reached
- Check `iteration_history` in status response to see progression

### Test 2: Verify Convergence

After analysis completes, check if it converged:

```bash
curl "http://localhost:8000/api/documents/$DOCUMENT_ID/status" | jq '.converged'
```

Expected: `true` (if gaps eliminated) or `false` (if max iterations reached)

### Test 3: Download Results

```bash
# Color-coded redraft (shows gaps in red, fixes in blue)
curl "http://localhost:8000/api/documents/$DOCUMENT_ID/redraft?mode=color_coded" \
  -o redraft_color.docx

# Clean redraft (production-ready, no markup)
curl "http://localhost:8000/api/documents/$DOCUMENT_ID/redraft?mode=clean" \
  -o redraft_clean.docx

# Compliance report (PDF with findings)
curl "http://localhost:8000/api/documents/$DOCUMENT_ID/report?format=pdf" \
  -o compliance_report.pdf
```

### Test 4: Query Findings by Error ID

```bash
# Get all findings (JSON)
curl "http://localhost:8000/api/documents/$DOCUMENT_ID/result" | jq '.high_confidence_findings[] | {finding_id, description, regulation_ref}'
```

Expected output:

```json
{
  "finding_id": "err-a3f2b1",
  "description": "Policy lacks explicit mention of...",
  "regulation_ref": "CARF Standard 1.A.1"
}
```

## 🔧 Configuration Profiles

### Profile 1: Fast Testing (Lower Precision)

```bash
MAX_ITERATIONS=2
HIGH_CONFIDENCE_THRESHOLD=0.85
ENABLE_CRITIQUE_SYSTEM=false
CONSENSUS_METHOD=agreement
```

**Use case:** Quick feedback during development

### Profile 2: Production (Balanced)

```bash
MAX_ITERATIONS=5
HIGH_CONFIDENCE_THRESHOLD=0.95
ENABLE_CRITIQUE_SYSTEM=true
CONSENSUS_METHOD=hybrid
```

**Use case:** Standard production deployment

### Profile 3: Maximum Precision (Slower)

```bash
MAX_ITERATIONS=5
HIGH_CONFIDENCE_THRESHOLD=0.98
ENABLE_CRITIQUE_SYSTEM=true
CONSENSUS_METHOD=hybrid
MIN_MODEL_AGREEMENT=0.80
```

**Use case:** Critical compliance documents requiring highest accuracy

## 📊 Understanding Iteration History

Each iteration in `iteration_history` shows:

```json
{
  "iteration": 0,
  "document_id": "...",
  "high_confidence_findings": 8,
  "medium_confidence_findings": 12,
  "converged": false,
  "timestamp": "2026-02-06T13:15:00.000Z"
}
```

**Example progression:**

- Iteration 0: 8 high-confidence gaps → generates redraft
- Iteration 1: 3 high-confidence gaps → generates redraft
- Iteration 2: 0 high-confidence gaps → ✅ **CONVERGED**

## 🎯 Next Steps

1. **Run the migration** (Step 2 above)
2. **Test with a sample document** to verify the system works
3. **Tune confidence thresholds** based on your precision requirements
4. **Enable/disable critique** based on performance vs. accuracy trade-offs
5. **Monitor API costs** - iterative mode uses more LLM calls

## 📖 Full Documentation

- [walkthrough.md](file:///home/oluwaseyi/.gemini/antigravity/brain/e8b65cb2-9676-4731-8596-667618d860af/walkthrough.md) - Complete implementation guide
- [implementation_plan.md](file:///home/oluwaseyi/.gemini/antigravity/brain/e8b65cb2-9676-4731-8596-667618d860af/implementation_plan.md) - Technical architecture details
- [WORK_PLAN.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/WORK_PLAN.md) - Original strategic vision

## 🐛 Troubleshooting

**Issue:** Migration fails

```bash
# Check current migration status
alembic current

# View migration history
alembic history
```

**Issue:** Analysis stuck in processing

```bash
# Check application logs
docker-compose logs -f app

# Or direct logs
tail -f logs/app.log
```

**Issue:** Never converges (infinite loop protection works)

- System automatically stops at MAX_ITERATIONS
- Last iteration's redraft is still available
- Review findings to understand persistent gaps

---

**Ready to deploy?** Start with Step 1 (environment variables) and follow the deployment steps above! 🚀
