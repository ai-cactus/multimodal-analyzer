# Multimodal-Analyzer: Comprehensive Cost Analysis

## Executive Summary

This document provides a detailed cost breakdown for the **multimodal-analyzer** system, covering all operational expenses including LLM API costs, Document AI processing, database storage, and infrastructure. The analysis focuses on **active/varying parameters** that directly impact costs and includes both **theoretical pricing** (based on 2026 API rates) and **estimated current usage patterns**.

---

## 1. LLM API Costs (Primary Cost Driver)

The system uses **Google Cloud Vertex AI Model Garden** to access three LLM models. Costs are primarily driven by **token usage** (input + output tokens).

### 1.1 Active LLM Models

| Model Key        | Full Model Name                            | Provider                       | Input Cost (per 1M tokens) | Output Cost (per 1M tokens) | Context Window | Max Output   |
| ---------------- | ------------------------------------------ | ------------------------------ | -------------------------- | --------------------------- | -------------- | ------------ |
| **llama-scout**  | `meta/llama-4-scout-17b-16e-instruct-maas` | Meta (OpenAI-compatible)       | **$0.25**                  | **$0.70**                   | ~327K tokens   | 8,192 tokens |
| **gemini-flash** | `gemini-2.0-flash-001`                     | Google Vertex AI               | **$0.15**                  | **$0.60**                   | 1M tokens      | 8,000 tokens |
| **gpt-oss**      | `openai/gpt-oss-120b-maas`                 | OpenAI OSS (OpenAI-compatible) | **$0.15**                  | **$0.60**                   | ~120K tokens   | 8,192 tokens |

> **Note**: Pricing is based on Google Cloud Vertex AI Model Garden (2026). Using Gemini API directly (outside Vertex AI) would be cheaper at $0.10/M input and $0.40/M output.

### 1.2 Active LLM Configuration Parameters

These parameters are **actively configured** in [`app/services/llm_client.py`](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/llm_client.py):

| Parameter            | Value                                         | Impact on Cost | Notes                                                               |
| -------------------- | --------------------------------------------- | -------------- | ------------------------------------------------------------------- |
| `temperature`        | **0.1**                                       | None (fixed)   | Low temperature for consistent outputs                              |
| `max_output_tokens`  | **8,192**                                     | **High**       | Directly limits output token cost per call                          |
| `USE_MULTI_MODEL`    | **true**                                      | **Very High**  | When true: uses all 3 models; when false: uses only `PRIMARY_MODEL` |
| `PRIMARY_MODEL`      | **llama-scout**                               | **Medium**     | Only relevant when `USE_MULTI_MODEL=false`                          |
| Retry attempts       | **5** (with exponential backoff)              | **Medium**     | Failed requests retry up to 5 times                                 |
| Concurrent LLM calls | **5** (semaphore limit)                       | None           | Rate limiting to prevent quota exhaustion                           |
| Timeout              | **120 seconds** (multi-LLM), **60s** (single) | None           | Prevents hung requests                                              |

### 1.3 Token Usage Estimation

Token usage varies significantly based on:

- **Document size** (pages, complexity)
- **Number of elements extracted**
- **Regulation context size** (top-k retrievals)
- **Number of iterations** (if refinement enabled)

#### Typical Token Usage per Analysis Element

| Component                   | Input Tokens (Estimate) | Output Tokens (Estimate) | Notes                                      |
| --------------------------- | ----------------------- | ------------------------ | ------------------------------------------ |
| System prompt               | 100-200                 | 0                        | Fixed analysis instructions                |
| Element content             | 200-2,000               | 0                        | Varies by element size (text/table/form)   |
| Regulation context (top-10) | 3,000-10,000            | 0                        | Retrieved regulations for compliance check |
| LLM response (findings)     | 0                       | 500-2,000                | JSON findings with compliance issues       |
| **Total per element**       | **3,500-12,000**        | **500-2,000**            | Single model, single element               |

#### Multi-LLM Multiplier

With `USE_MULTI_MODEL=true`, **all 3 models** analyze each element:

- **Total input tokens per element**: 3,500-12,000 × 3 = **10,500-36,000 tokens**
- **Total output tokens per element**: 500-2,000 × 3 = **1,500-6,000 tokens**

### 1.4 Cost Calculation: Per Document Analysis

#### Scenario 1: Small Document (10-page PDF, ~50 elements)

| Cost Component                                         | Calculation       | Subtotal   |
| ------------------------------------------------------ | ----------------- | ---------- |
| **Input tokens** (50 elements × 22,500 avg × 3 models) | 3,375,000 tokens  |            |
| - Llama Scout input                                    | 3.375M × $0.25/M  | **$0.84**  |
| - Gemini Flash input                                   | 3.375M × $0.15/M  | **$0.51**  |
| - GPT-OSS input                                        | 3.375M × $0.15/M  | **$0.51**  |
| **Output tokens** (50 elements × 3,750 avg × 3 models) | 562,500 tokens    |            |
| - Llama Scout output                                   | 0.5625M × $0.70/M | **$0.39**  |
| - Gemini Flash output                                  | 0.5625M × $0.60/M | **$0.34**  |
| - GPT-OSS output                                       | 0.5625M × $0.60/M | **$0.34**  |
| **Total LLM Cost (3 models)**                          |                   | **$2.93**  |
| **Single model cost** (if `USE_MULTI_MODEL=false`)     |                   | **~$0.98** |

#### Scenario 2: Medium Document (30-page PDF, ~150 elements)

| Cost Component                                          | Calculation       | Subtotal   |
| ------------------------------------------------------- | ----------------- | ---------- |
| **Input tokens** (150 elements × 22,500 avg × 3 models) | 10,125,000 tokens |            |
| - Llama Scout input                                     | 10.125M × $0.25/M | **$2.53**  |
| - Gemini Flash input                                    | 10.125M × $0.15/M | **$1.52**  |
| - GPT-OSS input                                         | 10.125M × $0.15/M | **$1.52**  |
| **Output tokens** (150 elements × 3,750 avg × 3 models) | 1,687,500 tokens  |            |
| - Llama Scout output                                    | 1.6875M × $0.70/M | **$1.18**  |
| - Gemini Flash output                                   | 1.6875M × $0.60/M | **$1.01**  |
| - GPT-OSS output                                        | 1.6875M × $0.60/M | **$1.01**  |
| **Total LLM Cost (3 models)**                           |                   | **$8.77**  |
| **Single model cost** (if `USE_MULTI_MODEL=false`)      |                   | **~$2.92** |

#### Scenario 3: Large Document (100-page PDF, ~500 elements)

| Cost Component                                          | Calculation       | Subtotal   |
| ------------------------------------------------------- | ----------------- | ---------- |
| **Input tokens** (500 elements × 22,500 avg × 3 models) | 33,750,000 tokens |            |
| - Llama Scout input                                     | 33.75M × $0.25/M  | **$8.44**  |
| - Gemini Flash input                                    | 33.75M × $0.15/M  | **$5.06**  |
| - GPT-OSS input                                         | 33.75M × $0.15/M  | **$5.06**  |
| **Output tokens** (500 elements × 3,750 avg × 3 models) | 5,625,000 tokens  |            |
| - Llama Scout output                                    | 5.625M × $0.70/M  | **$3.94**  |
| - Gemini Flash output                                   | 5.625M × $0.60/M  | **$3.38**  |
| - GPT-OSS output                                        | 5.625M × $0.60/M  | **$3.38**  |
| **Total LLM Cost (3 models)**                           |                   | **$29.26** |
| **Single model cost** (if `USE_MULTI_MODEL=false`)      |                   | **~$9.75** |

### 1.5 Additional LLM Costs: Critique System

The **critique system** (if `ENABLE_CRITIQUE_SYSTEM=true`) adds additional LLM calls:

| Parameter                      | Value            | Impact                                       |
| ------------------------------ | ---------------- | -------------------------------------------- |
| `ENABLE_CRITIQUE_SYSTEM`       | **true**         | Enables Proposer → Critic → Refiner workflow |
| `PROPOSER_MODEL`               | **gemini-flash** | Model that proposes initial findings         |
| `CRITIC_MODEL`                 | **llama-scout**  | Model that critiques findings                |
| `USE_CRITIQUE_IN_SINGLE_MODEL` | **true**         | Enables critique even with single model      |

**Cost Impact**: Critique adds **~30-50% more LLM API calls** on top of base analysis:

- Each finding is critiqued by the `CRITIC_MODEL`
- Refinement may trigger additional calls
- **Estimated critique overhead**: +$0.88 (small), +$2.63 (medium), +$8.78 (large)

### 1.6 Iterative Refinement Costs

| Parameter                     | Value    | Impact                                               |
| ----------------------------- | -------- | ---------------------------------------------------- |
| `MAX_ITERATIONS`              | **5**    | Maximum refinement loops                             |
| `CONVERGENCE_THRESHOLD`       | **0**    | Minimum improvement required to continue             |
| `HIGH_CONFIDENCE_THRESHOLD`   | **0.80** | Findings above this are considered high confidence   |
| `MEDIUM_CONFIDENCE_THRESHOLD` | **0.66** | Findings above this are considered medium confidence |

**Cost Multiplier**: Each iteration re-analyzes the document with redrafted content:

- **Iteration 1** (initial): Base cost
- **Iteration 2-5**: +100% of base cost per iteration for non-compliant documents
- **Total cost if max iterations reached**: **~6x base cost**

> **Example**: 30-page doc reaching 5 iterations: $8.77 × 6 = **$52.62**

---

## 2. Document AI Processing Costs

The system uses **Google Cloud Document AI** with two processors for document extraction.

### 2.1 Document AI Processors

| Processor Type    | Processor ID       | Cost per 1,000 Pages | Cost per Page | Purpose                                     |
| ----------------- | ------------------ | -------------------- | ------------- | ------------------------------------------- |
| **Layout Parser** | `32308c6036df50a2` | **$10.00**           | **$0.01**     | Extract structure, tables, paragraphs, text |
| **Form Parser**   | `41a5705cc8b8eb56` | **$30.00**           | **$0.03**     | Extract form fields, key-value pairs        |

> **Pricing Source**: Google Cloud Document AI pricing (2026), valid for first 1M pages/month. Volume pricing available for >1M pages.

### 2.2 Active Parameters

| Parameter           | Value                    | Impact on Cost                                          |
| ------------------- | ------------------------ | ------------------------------------------------------- |
| `DOCAI_LOCATION`    | **us**                   | Multi-region processor (no regional pricing difference) |
| Large file handling | **Chunk size: 15 pages** | PDFs >30 pages split into chunks                        |
| Fallback extraction | **PyPDF (free)**         | Used when Document AI fails (no AI cost)                |

### 2.3 Document AI Cost per Analysis

**Both processors are called for each document** (if form parser doesn't fail):

| Document Size | Pages | Layout Parser Cost  | Form Parser Cost    | Total Document AI Cost |
| ------------- | ----- | ------------------- | ------------------- | ---------------------- |
| Small         | 10    | 10 × $0.01 = $0.10  | 10 × $0.03 = $0.30  | **$0.40**              |
| Medium        | 30    | 30 × $0.01 = $0.30  | 30 × $0.03 = $0.90  | **$1.20**              |
| Large         | 100   | 100 × $0.01 = $1.00 | 100 × $0.03 = $3.00 | **$4.00**              |

**Note**: Form parser is optional (fails gracefully). If it fails, only layout parser cost applies.

### 2.4 Document AI for Large Files

For documents **>30 pages**, the system splits into **15-page chunks**:

- Each chunk is processed separately
- **Cost remains the same** (charged per page, not per API call)

---

## 3. Database Costs (PostgreSQL + pgvector)

The system uses **PostgreSQL with pgvector extension** for storing documents, regulations, embeddings, and findings.

### 3.1 Current Configuration (Docker Local)

From [`docker-compose.yml`](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/docker-compose.yml):

- **Image**: `pgvector/pgvector:pg16`
- **Local development**: No cloud costs (runs in Docker container)

### 3.2 Production Database Costs (Google Cloud SQL for PostgreSQL)

For production deployment on Google Cloud:

| Configuration            | vCPU | Memory  | Storage (SSD) | Monthly Cost (Estimate) |
| ------------------------ | ---- | ------- | ------------- | ----------------------- |
| **Small** (dev/testing)  | 1    | 3.75 GB | 50 GB         | **~$30-50**             |
| **Medium** (production)  | 4    | 15 GB   | 200 GB        | **~$180-250**           |
| **Large** (high traffic) | 8    | 30 GB   | 500 GB        | **~$400-600**           |

**Active cost drivers**:

- **Compute (vCPU + RAM)**: Billed per hour, varies by region
- **Storage**: ~$0.17/GB/month for SSD persistent disk
- **Backups**: Additional storage costs for automated backups
- **I/O operations**: Minimal cost for read/write operations

### 3.3 Database Storage Growth

| Data Type                  | Size per Document   | Notes                                     |
| -------------------------- | ------------------- | ----------------------------------------- |
| Uploaded document metadata | ~1 KB               | Basic info (filename, status, timestamps) |
| Document elements          | ~5-50 KB            | Structured elements from Document AI      |
| Analysis findings          | ~10-100 KB          | LLM findings with confidence scores       |
| Redrafts                   | ~50-500 KB          | Improved document versions                |
| Reports                    | ~10-50 KB           | Compliance reports                        |
| **Total per analysis**     | **~76 KB - 700 KB** | Average: ~200 KB per document             |

**Monthly storage estimate**:

- **100 documents/month**: ~20 MB storage growth
- **1,000 documents/month**: ~200 MB storage growth
- **10,000 documents/month**: ~2 GB storage growth

---

## 4. Redis Cache Costs

From [`docker-compose.yml`](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/docker-compose.yml):

- **Image**: `redis:7-alpine`
- **Local development**: No cloud costs

### 4.1 Production Redis Costs (Google Cloud Memorystore)

| Tier                 | Capacity | Hourly Cost   | Monthly Cost (730 hrs) |
| -------------------- | -------- | ------------- | ---------------------- |
| **Basic M1**         | 1 GB     | $0.027/GiB/hr | **~$20**               |
| **Basic M2**         | 5 GB     | $0.027/GiB/hr | **~$100**              |
| **Standard M1** (HA) | 1 GB     | $0.054/GiB/hr | **~$40**               |
| **Standard M2** (HA) | 5 GB     | $0.054/GiB/hr | **~$200**              |

**Note**: Standard tier provides high availability with replication.

---

## 5. Cloud Infrastructure Costs

### 5.1 Compute Engine (VM for Application)

The FastAPI application runs on a VM instance:

| Instance Type            | vCPU | Memory | Monthly Cost (us-east5)     |
| ------------------------ | ---- | ------ | --------------------------- |
| **e2-micro** (Free Tier) | 0.25 | 1 GB   | **$0** (Free Tier eligible) |
| **e2-small**             | 1    | 2 GB   | **~$15**                    |
| **e2-medium**            | 2    | 4 GB   | **~$30**                    |
| **e2-standard-4**        | 4    | 16 GB  | **~$120**                   |

**Free Tier**: 1 non-preemptible e2-micro instance per month in select US regions.

### 5.2 Cloud Storage Costs

For storing uploaded documents and generated reports:

| Storage Class             | Cost per GB/month | Retrieval Cost |
| ------------------------- | ----------------- | -------------- |
| **Standard**              | $0.020            | Free           |
| **Nearline** (30-day min) | $0.010            | $0.01/GB       |
| **Coldline** (90-day min) | $0.004            | $0.02/GB       |

**Estimated monthly storage** (1,000 documents):

- Average document size: 2 MB
- Total storage: ~2 GB
- **Cost**: 2 GB × $0.020 = **$0.04/month** (Standard class)

### 5.3 Network Egress Costs

| Traffic Type                             | Cost                         |
| ---------------------------------------- | ---------------------------- |
| Within same region                       | Free                         |
| Between regions (North America)          | $0.01/GB                     |
| Internet egress (worldwide)              | $0.08-0.12/GB                |
| CDN Interconnect (effective May 1, 2026) | **$0.08/GB** (North America) |

**Estimated network costs**: Minimal for typical usage (<10 GB/month).

---

## 6. Total Cost per Document Analysis

Combining all cost components:

### 6.1 Cost Breakdown by Document Size

#### Small Document (10 pages)

| Cost Component               | Multi-Model | Single Model |
| ---------------------------- | ----------- | ------------ |
| LLM API (base)               | **$2.93**   | **$0.98**    |
| + Critique system            | +$0.88      | +$0.29       |
| + Redrafting                 | +$0.15      | +$0.05       |
| Document AI                  | **$0.40**   | **$0.40**    |
| Database (negligible)        | $0.00       | $0.00        |
| **Total per analysis**       | **$4.36**   | **$1.72**    |
| **With max iterations (5x)** | **$20.52**  | **$7.62**    |

#### Medium Document (30 pages)

| Cost Component               | Multi-Model | Single Model |
| ---------------------------- | ----------- | ------------ |
| LLM API (base)               | **$8.77**   | **$2.92**    |
| + Critique system            | +$2.63      | +$0.88       |
| + Redrafting                 | +$0.45      | +$0.15       |
| Document AI                  | **$1.20**   | **$1.20**    |
| Database (negligible)        | $0.00       | $0.00        |
| **Total per analysis**       | **$13.05**  | **$5.15**    |
| **With max iterations (5x)** | **$61.53**  | **$23.55**   |

#### Large Document (100 pages)

| Cost Component               | Multi-Model | Single Model |
| ---------------------------- | ----------- | ------------ |
| LLM API (base)               | **$29.26**  | **$9.75**    |
| + Critique system            | +$8.78      | +$2.93       |
| + Redrafting                 | +$1.50      | +$0.50       |
| Document AI                  | **$4.00**   | **$4.00**    |
| Database (negligible)        | $0.00       | $0.00        |
| **Total per analysis**       | **$43.54**  | **$17.18**   |
| **With max iterations (5x)** | **$205.23** | **$78.54**   |

### 6.2 Monthly Infrastructure Baseline

These costs apply **regardless of document volume**:

| Service                    | Configuration     | Monthly Cost |
| -------------------------- | ----------------- | ------------ |
| Compute Engine             | e2-medium VM      | **$30**      |
| Cloud SQL (PostgreSQL)     | 4 vCPU, 15 GB RAM | **$180**     |
| Memorystore (Redis)        | Basic 1 GB        | **$20**      |
| Cloud Storage              | 10 GB             | **$0.20**    |
| **Total Monthly Baseline** |                   | **$230.20**  |

---

## 7. Active/Varying Cost Parameters Summary

These parameters have the **highest impact on costs** and should be monitored closely:

### 7.1 Configuration-Based Parameters (`.env`)

| Parameter                | Current Value   | Cost Impact       | Recommendations                                   |
| ------------------------ | --------------- | ----------------- | ------------------------------------------------- |
| `USE_MULTI_MODEL`        | **true**        | **3x cost**       | Set to `false` for cost savings, use single model |
| `PRIMARY_MODEL`          | **llama-scout** | Medium            | Switch to `gemini-flash` for 40% savings          |
| `ENABLE_CRITIQUE_SYSTEM` | **true**        | **+30-50%**       | Disable for cost savings if accuracy allows       |
| `MAX_ITERATIONS`         | **5**           | **Up to 6x cost** | Reduce to 2-3 for cost control                    |
| `CONVERGENCE_THRESHOLD`  | **0**           | High              | Increase to 0.05-0.10 to stop early iterations    |
| `max_output_tokens`      | **8,192**       | High              | Reduce to 4096 if outputs are typically shorter   |

### 7.2 Usage-Based Parameters

| Parameter                           | Impact    | Notes                                 |
| ----------------------------------- | --------- | ------------------------------------- |
| **Document page count**             | Very High | Linear scaling with Document AI costs |
| **Document complexity** (elements)  | Very High | More elements = more LLM calls        |
| **Regulation context size** (top-k) | High      | More context = more input tokens      |
| **Number of findings**              | Medium    | More findings = more critique calls   |
| **Redraft iterations**              | Very High | Each iteration multiplies LLM costs   |

---

## 8. Cost Optimization Recommendations

### 8.1 Immediate Cost Reductions

| Action                                | Savings                    | Trade-off                         |
| ------------------------------------- | -------------------------- | --------------------------------- |
| Set `USE_MULTI_MODEL=false`           | **-66%** on LLM            | Lower consensus accuracy          |
| Set `PRIMARY_MODEL=gemini-flash`      | **-40%** on LLM            | Slightly different model behavior |
| Set `ENABLE_CRITIQUE_SYSTEM=false`    | **-30-50%** on LLM         | Fewer false positive findings     |
| Reduce `MAX_ITERATIONS` to 2          | **-50%** on iterative docs | May miss some compliance issues   |
| Reduce `max_output_tokens` to 4096    | **-50%** on output         | Limits finding detail             |
| Use layout parser only (disable form) | **-75%** on Document AI    | Loss of form field extraction     |

### 8.2 Cost Monitoring Metrics

Track these metrics to monitor and control costs:

- **Average tokens per analysis** (input + output)
- **Average iterations per document** (should be <2 ideally)
- **Document AI pages processed** (monthly total)
- **LLM API call count** (by model)
- **Failed LLM calls** (retries add cost)

### 8.3 Cost-Effective Configurations

#### Budget Configuration (Low Cost)

```env
USE_MULTI_MODEL=false
PRIMARY_MODEL=gemini-flash
ENABLE_CRITIQUE_SYSTEM=false
MAX_ITERATIONS=2
max_output_tokens=4096
```

**Estimated cost**: $1.72 (10-page), $5.15 (30-page), $17.18 (100-page)

#### Balanced Configuration (Current)

```env
USE_MULTI_MODEL=true
ENABLE_CRITIQUE_SYSTEM=true
MAX_ITERATIONS=5
max_output_tokens=8192
```

**Estimated cost**: $4.36 (10-page), $13.05 (30-page), $43.54 (100-page)

#### Premium Configuration (High Accuracy)

```env
USE_MULTI_MODEL=true
ENABLE_CRITIQUE_SYSTEM=true
MAX_ITERATIONS=5
HIGH_CONFIDENCE_THRESHOLD=0.85
```

**Estimated cost**: Same as balanced, but higher iteration frequency → up to **$20-205** per doc

---

## 9. Monthly Cost Projections

### 9.1 Scenario: 100 Documents/Month (Mixed Sizes)

Assuming:

- 40% small (10 pages)
- 40% medium (30 pages)
- 20% large (100 pages)
- Average 1.5 iterations per document
- Multi-model enabled

| Cost Component          | Calculation            | Monthly Cost  |
| ----------------------- | ---------------------- | ------------- |
| LLM API (small)         | 40 docs × $4.36 × 1.5  | **$261.60**   |
| LLM API (medium)        | 40 docs × $13.05 × 1.5 | **$783.00**   |
| LLM API (large)         | 20 docs × $43.54 × 1.5 | **$1,306.20** |
| Document AI (small)     | 40 × $0.40             | **$16.00**    |
| Document AI (medium)    | 40 × $1.20             | **$48.00**    |
| Document AI (large)     | 20 × $4.00             | **$80.00**    |
| Infrastructure baseline |                        | **$230.20**   |
| **Total Monthly Cost**  |                        | **$2,725.00** |

**Cost per document average**: $27.25

### 9.2 Scenario: 1,000 Documents/Month

| Cost Component            | Monthly Cost   |
| ------------------------- | -------------- |
| LLM API                   | **$23,508.00** |
| Document AI               | **$1,440.00**  |
| Infrastructure (+storage) | **$280.00**    |
| **Total Monthly Cost**    | **$25,228.00** |

**Cost per document average**: $25.23 (economies of scale)

---

## 10. Key Figures Reference Table

### Quick Reference: Cost per 1M Tokens

| Model        | Input | Output | Weighted Avg (60/40 split) |
| ------------ | ----- | ------ | -------------------------- |
| Llama Scout  | $0.25 | $0.70  | **$0.43**                  |
| Gemini Flash | $0.15 | $0.60  | **$0.33**                  |
| GPT-OSS      | $0.15 | $0.60  | **$0.33**                  |

### Quick Reference: Average Tokens per Analysis

| Document Size  | Avg Input Tokens (3 models) | Avg Output Tokens (3 models) |
| -------------- | --------------------------- | ---------------------------- |
| Small (10 pg)  | 3.375M                      | 0.5625M                      |
| Medium (30 pg) | 10.125M                     | 1.6875M                      |
| Large (100 pg) | 33.75M                      | 5.625M                       |

### Quick Reference: Document AI Costs

| Pages | Layout | Form  | Total     |
| ----- | ------ | ----- | --------- |
| 10    | $0.10  | $0.30 | **$0.40** |
| 30    | $0.30  | $0.90 | **$1.20** |
| 100   | $1.00  | $3.00 | **$4.00** |

---

## Appendix: Cost Calculation Formulas

### LLM Cost Formula

```
Total LLM Cost = (
    (Input Tokens × Model Input Rate) +
    (Output Tokens × Model Output Rate)
) × Number of Models × (1 + Critique Overhead) × Iterations
```

### Document AI Cost Formula

```
Document AI Cost = (
    Pages × Layout Parser Rate +
    Pages × Form Parser Rate
)
```

### Total Analysis Cost Formula

```
Total Cost = LLM Cost + Document AI Cost + (Infrastructure / Monthly Docs)
```

---

**Document Version**: 1.0  
**Last Updated**: February 9, 2026  
**System Configuration**: [`/home/oluwaseyi/dev247/official/multimodal-analyzer/.env`](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/.env)
