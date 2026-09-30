# Multimodal Analyzer - Comprehensive Project Documentation

**Version:** 1.0.0  
**Last Updated:** February 8, 2026  
**Status:** Phase 1 Complete (Infrastructure & Extraction)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Technologies & Tools](#core-technologies--tools)
4. [Multi-LLM Analysis System](#multi-llm-analysis-system)
5. [Workflows & Pipelines](#workflows--pipelines)
6. [API Architecture](#api-architecture)
7. [Database Schema](#database-schema)
8. [Configuration & Environment Setup](#configuration--environment-setup)
9. [Processing Configuration](#processing-configuration)
10. [Deployment & Operations](#deployment--operations)
11. [Document Processing Capabilities](#document-processing-capabilities)
12. [Development Workflow](#development-workflow)

---

## Executive Summary

### Project Overview

The **Multimodal Analyzer** is a high-performance AI-powered compliance analysis service designed for healthcare and behavioral health organizations. It analyzes policy documents against regulatory standards (CARF, MHRS, DBH) using advanced multi-LLM consensus technology to identify compliance gaps and generate compliant document redrafts.

### Key Capabilities

- **Multi-LLM Consensus Analysis**: Leverages Gemini 2.0 Flash, Llama Scout, and GPT-OSS models for high-confidence findings
- **Structure-Preserving Extraction**: Uses GCP Document AI to extract text, tables, forms, and hierarchical structures with coordinate tracking
- **Intelligent Critique System**: Proposer-Critic-Refiner workflow for iterative refinement
- **Confidence-Based Scoring**: Multi-dimensional scoring (≥0.95 threshold) with model agreement, grounding, and semantic consistency
- **Automated Redrafting**: Color-coded document redrafts with tracked changes
- **Comprehensive Reporting**: Detailed compliance reports with regulation citations and remediation suggestions

### Technology Stack Summary

| Layer              | Technologies                                        |
| ------------------ | --------------------------------------------------- |
| **Backend**        | FastAPI, Python 3.10+, asyncio                      |
| **Database**       | PostgreSQL 16 + pgvector, Redis 7+                  |
| **AI/ML**          | Google Vertex AI, Document AI, LangGraph, LangChain |
| **Models**         | Gemini 2.0 Flash, Llama Scout, GPT-OSS              |
| **Infrastructure** | Docker, Docker Compose, GCP                         |
| **Storage**        | PostgreSQL (primary), Redis (caching/queue)         |

### Current Development Status

**✅ Phase 1 Complete: Infrastructure & Extraction**

- FastAPI application with async SQLAlchemy 2.0
- PostgreSQL with pgvector for embeddings
- GCP Document AI integration
- Vertex AI embedding service
- Multi-standard section parser (CARF, MHRS, DBH)
- Regulation ingestion workflow
- Multi-LLM consensus engine
- Iterative refinement with critique system
- Output generation (DOCX, PDF, JSON)

**🚧 Future Phases:**

- Phase 2-7: Advanced orchestration, optimization, and production deployment

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[API Clients / Postman]
    end

    subgraph "API Layer - FastAPI"
        API[REST API Endpoints]
        REG[Regulations API]
        DOC[Documents API]
    end

    subgraph "Extraction Layer - GCP"
        DOCAI[Document AI<br/>Layout & Form Parser]
        PARSER[Compliance Section Parser<br/>CARF, MHRS, DBH]
    end

    subgraph "Processing Layer"
        ANALYSIS[Analysis Service]
        ITERATIVE[Iterative Analysis Engine]
        CONSENSUS[Consensus Engine]
        CRITIQUE[Critique System<br/>Proposer→Critic→Refiner]
    end

    subgraph "AI/ML Layer - Vertex AI"
        LLM[Multi-LLM Client]
        GEMINI[Gemini 2.0 Flash]
        LLAMA[Llama Scout]
        GPT[GPT-OSS]
        EMBED[Embedding Service<br/>text-embedding-005]
    end

    subgraph "Output Layer"
        FORMATTER[Output Formatter]
        DOCX[DOCX Generator]
        PDF[PDF Generator]
        JSON[JSON Formatter]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL + pgvector)]
        REDIS[(Redis Cache)]
    end

    CLIENT --> API
    API --> REG
    API --> DOC

    REG --> DOCAI
    DOC --> DOCAI

    DOCAI --> PARSER
    PARSER --> DB

    DOC --> ANALYSIS
    ANALYSIS --> ITERATIVE
    ITERATIVE --> LLM
    ITERATIVE --> CONSENSUS
    ITERATIVE --> CRITIQUE

    LLM --> GEMINI
    LLM --> LLAMA
    LLM --> GPT

    CONSENSUS --> FORMATTER
    FORMATTER --> DOCX
    FORMATTER --> PDF
    FORMATTER --> JSON

    ANALYSIS --> EMBED
    EMBED --> DB

    REDIS -.-> LLM
    REDIS -.-> ANALYSIS
```

### Component Overview

#### 1. **API Layer** ([main.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/main.py))

- **FastAPI Application**: RESTful API with async support
- **CORS Middleware**: Cross-origin resource sharing enabled
- **Health Checks**: `/health` and `/` endpoints
- **Prometheus Metrics**: `/metrics` endpoint for monitoring

#### 2. **Extraction Layer**

- **Document AI**: GCP's Layout and Form parsers for structure preservation
- **Section Parser**: Custom logic for CARF (hierarchical) and MHRS/DBH (legal) numbering

#### 3. **Processing Layer**

- **Analysis Service**: Orchestrates the complete workflow
- **Iterative Analysis**: Automatically refines documents up to 5 iterations
- **Consensus Engine**: Clusters findings using semantic similarity (DBSCAN)
- **Critique System**: Multi-LLM critique workflow for validation

#### 4. **AI/ML Layer**

- **Multi-LLM Client**: Manages Gemini, Llama, and GPT-OSS models
- **Vertex AI Integration**: Enterprise-grade model access
- **Embedding Service**: Generates semantic embeddings for RAG

#### 5. **Output Layer**

- **DOCX Generator**: Color-coded Word documents
- **PDF Generator**: ReportLab-based PDF generation
- **JSON Formatter**: Structured data output

#### 6. **Data Layer**

- **PostgreSQL**: Primary data store with pgvector extension
- **Redis**: Caching and task queue

---

## Core Technologies & Tools

### Backend Framework

**FastAPI** (v0.115.6+)

- Async-first architecture
- Auto-generated OpenAPI/Swagger documentation
- Pydantic schema validation
- High performance (comparable to NodeJS, Go)

**Key Files:**

- [app/main.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/main.py) - Application entry point
- [app/config.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/config.py) - Configuration management
- [app/database.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/database.py) - Database setup

### Database Systems

#### PostgreSQL 16 + pgvector

- **Primary Database**: Stores documents, regulations, findings, and analysis results
- **pgvector Extension**: Enables vector similarity search for RAG
- **Async Driver**: asyncpg for non-blocking queries
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic for schema versioning

**Configuration:**

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:6384/rag_analyzer
```

#### Redis 7+

- **Caching**: LLM response caching
- **Task Queue**: Asynchronous job processing
- **Session Storage**: Temporary state management

**Configuration:**

```bash
REDIS_URL=redis://localhost:6383/0
```

### Google Cloud Platform Services

#### Document AI

- **Layout Parser**: Extracts text, tables, forms, and structural elements
- **Form Parser**: Identifies key-value pairs and form fields
- **Coordinate Tracking**: Preserves bounding boxes for grounding verification

**Processor IDs:**

- Layout Processor: `32308c6036df50a2`
- Form Processor: `41a5705cc8b8eb56`

#### Vertex AI

- **Model Garden**: Access to enterprise LLMs (Gemini, Claude, Llama)
- **Embedding API**: `text-embedding-005` for semantic search
- **Regional Endpoints**: Model-specific regions for optimization

**Model Regions:**
| Model | Region |
|-------|--------|
| Gemini 2.0 Flash | us-central1 |
| Llama Scout | us-east5 |
| GPT-OSS | global |
| Claude Opus | global |

### AI/ML Platforms and Models

#### LangChain Ecosystem (v1.x)

- **LangChain**: Framework for LLM applications
- **LangGraph**: State machine orchestration
- **LangChain Google Vertex AI**: Native Vertex AI integration
- **LangChain Community**: Additional tools and utilities

#### Multi-LLM Configuration

**Primary Models:**

1. **Llama Scout** (`meta/llama-3.2-90b-vision-instruct-maas`)
   - Region: us-east5
   - Best for: General analysis
2. **Gemini 2.0 Flash** (`gemini-2.0-flash-001`)
   - Region: us-central1
   - Best for: RAG-optimized analysis
3. **GPT-OSS** (`gpt-4-turbo` via OpenAI on Vertex)
   - Region: global
   - Best for: Alternative perspective

**Model Client:** [app/services/llm_client.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/llm_client.py)

### Development and Deployment Tools

#### Docker & Docker Compose

- **PostgreSQL Container**: pgvector/pgvector:pg16
- **Redis Container**: redis:7-alpine
- **Volume Management**: Persistent storage for databases

**Docker Compose File:** [docker-compose.yml](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/docker-compose.yml)

#### Python Dependencies

- **Core**: FastAPI, Uvicorn, Pydantic
- **Database**: SQLAlchemy, asyncpg, Alembic, pgvector
- **GCP**: google-cloud-documentai, google-cloud-aiplatform
- **ML**: scikit-learn, numpy
- **Output**: python-docx, reportlab, pypdf
- **Utilities**: tenacity (retry logic), python-json-logger

**Requirements:** [requirements.txt](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/requirements.txt)

---

## Multi-LLM Analysis System

### Architecture Overview

The system uses a **consensus-based approach** where multiple LLMs analyze the same content independently, and their findings are clustered and scored for confidence.

```mermaid
graph LR
    INPUT[Document Element] --> GEMINI[Gemini Analysis]
    INPUT --> LLAMA[Llama Analysis]
    INPUT --> GPT[GPT Analysis]

    GEMINI --> CLUSTER[Semantic Clustering<br/>DBSCAN]
    LLAMA --> CLUSTER
    GPT --> CLUSTER

    CLUSTER --> SCORE[Confidence Scoring<br/>Agreement + Grounding]

    SCORE --> HIGH[High Confidence<br/>≥0.95]
    SCORE --> MEDIUM[Medium Confidence<br/>0.80-0.95]
    SCORE --> LOW[Low Confidence<br/><0.80]

    HIGH --> OUTPUT[Final Report]
    MEDIUM --> OUTPUT
    LOW -.-> DISCARD[Discarded]
```

### LLM Model Configuration

**Location:** [app/services/llm_client.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/llm_client.py)

**Model Selection Modes:**

1. **Multi-Model Mode** (`USE_MULTI_MODEL=true`)
   - Uses all available models for consensus
   - Higher confidence, slower processing
   - Recommended for production

2. **Single-Model Mode** (`USE_MULTI_MODEL=false`)
   - Uses only `PRIMARY_MODEL`
   - Faster, cheaper processing
   - Can still use critique system (self-critique)

### Consensus Engine Architecture

**Location:** [app/services/consensus_engine.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/consensus_engine.py)

#### Semantic Clustering Process

1. **Extract Findings**: Collect all findings from all models
2. **Generate Embeddings**: Create semantic embeddings for each finding
3. **DBSCAN Clustering**: Group semantically similar findings (eps=0.12, cosine distance)
4. **Cluster Analysis**: Identify which models agree on each finding

#### Confidence Scoring System

**Multi-Dimensional Score Formula:**

```
Confidence = 0.50 × Agreement + 0.30 × Grounding + 0.10 × Citation + 0.10 × Consistency
```

**Components:**

| Component       | Weight | Description                                          |
| --------------- | ------ | ---------------------------------------------------- |
| **Agreement**   | 50%    | Percentage of models that identified the finding     |
| **Grounding**   | 30%    | Percentage of claim verifiable in source coordinates |
| **Citation**    | 10%    | Quality and specificity of regulation reference      |
| **Consistency** | 10%    | Semantic similarity of findings (1 - std_dev)        |

**Confidence Thresholds:**

```env
HIGH_CONFIDENCE_THRESHOLD=0.95   # Auto-include in report
MEDIUM_CONFIDENCE_THRESHOLD=0.80 # Include but flag for review
```

Findings below 0.80 are automatically discarded as low confidence.

### Critique and Iterative Refinement Workflow

**Location:** [app/services/critique_engine.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/critique_engine.py), [app/services/iterative_analysis.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/iterative_analysis.py)

#### Critique System Flow

```mermaid
graph TD
    START[Original Document] --> PROPOSER[Proposer Model<br/>Gemini Flash]
    PROPOSER --> FINDINGS[Initial Findings]
    FINDINGS --> CRITIC[Critic Model<br/>Llama Scout]
    CRITIC --> VALIDATE{Validate Findings}
    VALIDATE -->|Valid| KEEP[Keep Finding]
    VALIDATE -->|Invalid| REFINE[Refine Finding]
    VALIDATE -->|False Positive| REJECT[Reject Finding]
    KEEP --> REDRAFT[Generate Redraft]
    REFINE --> REDRAFT
    REJECT -.-> REDRAFT
```

#### Iterative Refinement Process

**Maximum Iterations:** 5 (configurable via `MAX_ITERATIONS`)  
**Convergence Threshold:** 0 high-confidence findings (perfect compliance)

**Workflow:**

1. **Initial Analysis**: Analyze original document
2. **Generate Redraft**: Create compliant version based on findings
3. **Re-analyze Redraft**: Run analysis on redrafted document
4. **Compare Results**: Check if findings decreased
5. **Iterate**: Repeat until convergence or max iterations reached

**Configuration:**

```env
MAX_ITERATIONS=5
CONVERGENCE_THRESHOLD=0
ENABLE_CRITIQUE_SYSTEM=true
PROPOSER_MODEL=gemini-flash
CRITIC_MODEL=llama-scout
USE_CRITIQUE_IN_SINGLE_MODEL=true
```

---

## Workflows & Pipelines

### Regulation Ingestion Workflow

**Endpoint:** `POST /api/regulations/upload`

```mermaid
graph TD
    UPLOAD[Upload Regulation PDF/DOCX] --> EXTRACT[Document AI Extraction]
    EXTRACT --> PARSE[Section Parser<br/>CARF/MHRS/DBH]
    PARSE --> CHUNK[Chunk by Section]
    CHUNK --> EMBED[Generate Embeddings<br/>Vertex AI]
    EMBED --> STORE[Store in PostgreSQL<br/>regulation_texts table]
    STORE --> INDEX[Create Vector Index]
    INDEX --> COMPLETE[Status: Completed]
```

**Process Steps:**

1. **Upload**: Accept compliance manual (CARF, MHRS, DBH)
2. **Extract**: Use Document AI to extract text and structure
3. **Parse**: Apply compliance-body-specific parsing logic
4. **Chunk**: Split into sections with regex-based identification
5. **Embed**: Generate semantic embeddings for vector search
6. **Store**: Save to `regulation_documents` and `regulation_texts` tables
7. **Index**: Create pgvector indexes for similarity search

### Document Analysis Pipeline

**Endpoint:** `POST /api/documents/analyze`

```mermaid
graph TD
    SUBMIT[Submit Document] --> EXTRACT[Document AI<br/>Extract Elements]
    EXTRACT --> RETRIEVE[Retrieve Relevant<br/>Regulations via RAG]
    RETRIEVE --> ANALYZE[Multi-LLM Analysis<br/>Gemini + Llama + GPT]
    ANALYZE --> CONSENSUS[Consensus Engine<br/>Cluster & Score]
    CONSENSUS --> CRITIQUE[Critique System<br/>Validate Findings]
    CRITIQUE --> REDRAFT[Generate Redraft]
    REDRAFT --> REANALYZE{Re-analyze<br/>Redraft?}
    REANALYZE -->|Iterations < MAX| ANALYZE
    REANALYZE -->|Converged/Max| REPORT[Generate Report]
    REPORT --> OUTPUT[Output Files<br/>DOCX, PDF, JSON]
```

**Detailed Steps:**

1. **Document Upload**: Client submits policy document
2. **Status: Processing**: Create database record
3. **Extraction**: Document AI extracts elements (tables, forms, text, lists)
4. **Element Storage**: Save to `document_elements` table
5. **RAG Retrieval**: For each element, retrieve relevant regulations using vector similarity
6. **Multi-LLM Analysis**: Run parallel analysis across all active models
7. **Consensus Building**: Cluster findings and calculate confidence scores
8. **Critique Validation**: Proposer-Critic workflow validates findings
9. **Redraft Generation**: Create compliant version of document
10. **Iterative Refinement**: Re-analyze redraft (up to 5 iterations)
11. **Report Synthesis**: Generate compliance report with citations
12. **Output Generation**: Create DOCX, PDF, and JSON outputs
13. **Status: Completed**: Update database status

**Location:** [app/services/analysis_service.py](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/services/analysis_service.py)

### Multi-LLM Consensus Workflow

```mermaid
graph LR
    PROMPT[Analysis Prompt] --> P1[Parallel Execution]
    P1 --> G[Gemini]
    P1 --> L[Llama]
    P1 --> O[GPT-OSS]

    G --> E1[Embedding]
    L --> E2[Embedding]
    O --> E3[Embedding]

    E1 --> DBSCAN[DBSCAN Clustering]
    E2 --> DBSCAN
    E3 --> DBSCAN

    DBSCAN --> C1[Cluster 1: 3/3 agree]
    DBSCAN --> C2[Cluster 2: 2/3 agree]
    DBSCAN --> C3[Cluster 3: 1/3 only]

    C1 --> S1[Score: 0.96 HIGH]
    C2 --> S2[Score: 0.85 MEDIUM]
    C3 --> S3[Score: 0.68 LOW]
```

**Consensus Methods:**

| Method       | Description                        | Use Case                       |
| ------------ | ---------------------------------- | ------------------------------ |
| `agreement`  | Pure model agreement percentage    | Simple majority voting         |
| `confidence` | Average of model confidence scores | When models provide confidence |
| `hybrid`     | Weighted combination (default)     | Production use                 |

**Configuration:**

```env
CONSENSUS_METHOD=hybrid
MIN_MODEL_AGREEMENT=0.66  # Require 2/3 models to agree
```

---

## API Architecture

### REST API Endpoints

**Base URL:** `http://localhost:8000`  
**Documentation:**

- Swagger UI: `/docs`
- ReDoc: `/redoc`

#### Core Endpoints

**Health & Status**

```http
GET /
GET /health
GET /metrics  # Prometheus metrics
```

#### Regulations Management

**Upload Regulation Manual**

```http
POST /api/regulations/upload
Content-Type: multipart/form-data

Parameters:
- file: (file) PDF or DOCX regulation document
- compliance_body: (string) "CARF" | "MHRS" | "DBH"
- version: (string) e.g., "2025"
- effective_date: (string, optional) YYYY-MM-DD
```

**Response:**

```json
{
  "regulation_id": "uuid",
  "compliance_body": "CARF",
  "status": "processing",
  "total_pages": null,
  "estimated_completion": "2026-02-08T17:00:00Z"
}
```

**Check Regulation Status**

```http
GET /api/regulations/{regulation_id}/status
```

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
  "created_at": "2026-02-08T16:30:00Z",
  "completed_at": "2026-02-08T16:45:00Z"
}
```

#### Document Analysis

**Submit Document for Analysis**

```http
POST /api/documents/analyze
Content-Type: multipart/form-data

Parameters:
- file: (file) Policy document (PDF, DOCX)
- compliance_body: (string) "CARF" | "MHRS" | "DBH"
- output_formats: (array, optional) ["docx", "pdf", "json"]
```

**Response:**

```json
{
  "document_id": "uuid",
  "status": "processing",
  "estimated_completion": "2026-02-08T17:30:00Z"
}
```

**Check Analysis Status**

```http
GET /api/documents/{document_id}/status
```

**Get Analysis Results (JSON)**

```http
GET /api/documents/{document_id}/result
```

**Response Structure:**

```json
{
  "document_id": "uuid",
  "status": "completed",
  "analysis_summary": {
    "high_confidence_findings": [...],
    "medium_confidence_findings": [...],
    "total_findings": 12,
    "compliance_score": 87.5,
    "iterations_completed": 3
  },
  "findings": [
    {
      "finding_id": "uuid",
      "error_id": "ERR-3409-001",
      "section": "Section 3.2",
      "severity": "critical",
      "description": "Missing required complaint resolution timeline",
      "regulation_ref": "§3409.4(a)",
      "confidence_score": 0.96,
      "model_agreement": "3/3",
      "critique_trail": [...]
    }
  ]
}
```

**Download Report**

```http
GET /api/documents/{document_id}/report?format=docx
```

**Download Redraft**

```http
GET /api/documents/{document_id}/redraft?mode=color_coded&format=docx
```

**Parameters:**

- `mode`: `color_coded` | `clean`
- `format`: `docx` | `pdf` | `json`

### Authentication and Authorization

**Current Status:** Not implemented (Phase 1)  
**Planned:** JWT-based authentication with role-based access control

### Rate Limiting and Quotas

**Current Status:** Not implemented (Phase 1)  
**Planned:** Redis-based rate limiting per API key

---

## Database Schema

### Core Data Models

**Location:** [app/models/](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/app/models/)

#### Compliance Bodies

**Table:** `compliance_bodies`

| Column      | Type         | Description            |
| ----------- | ------------ | ---------------------- |
| id          | Integer (PK) | Primary key            |
| name        | String(50)   | "CARF", "MHRS", "DBH"  |
| full_name   | String(200)  | Full organization name |
| description | Text         | Body description       |
| created_at  | Timestamp    | Creation timestamp     |

#### Regulation Documents

**Table:** `regulation_documents`

| Column             | Type         | Description                    |
| ------------------ | ------------ | ------------------------------ |
| id                 | UUID (PK)    | Primary key                    |
| compliance_body_id | Integer (FK) | Reference to compliance_bodies |
| version            | String(50)   | e.g., "2025"                   |
| effective_date     | Date         | When regulation takes effect   |
| file_path          | String(500)  | Storage path                   |
| total_pages        | Integer      | Page count                     |
| status             | String(50)   | processing, completed, failed  |
| created_at         | Timestamp    | Upload timestamp               |
| completed_at       | Timestamp    | Processing completion          |

#### Regulation Texts

**Table:** `regulation_texts`

| Column        | Type        | Description                       |
| ------------- | ----------- | --------------------------------- |
| id            | UUID (PK)   | Primary key                       |
| regulation_id | UUID (FK)   | Reference to regulation_documents |
| section_ref   | Text        | e.g., "1.L.1.b.(4)" or "§3409.4"  |
| text          | Text        | Regulation content                |
| embedding     | Vector(768) | Semantic embedding (pgvector)     |
| metadata      | JSONB       | Additional structured data        |
| created_at    | Timestamp   | Creation timestamp                |

**Indexes:**

- `idx_regulation_embedding`: GiST index on embedding for similarity search
- `idx_regulation_section`: B-tree index on section_ref

#### Uploaded Documents

**Table:** `uploaded_documents`

| Column             | Type         | Description                   |
| ------------------ | ------------ | ----------------------------- |
| id                 | UUID (PK)    | Primary key                   |
| filename           | String(500)  | Original filename             |
| file_path          | String(500)  | Storage path                  |
| compliance_body_id | Integer (FK) | Target compliance body        |
| status             | String(50)   | processing, completed, failed |
| current_step       | String(100)  | Current processing step       |
| total_pages        | Integer      | Page count                    |
| created_at         | Timestamp    | Upload timestamp              |
| completed_at       | Timestamp    | Processing completion         |

#### Document Elements

**Table:** `document_elements`

| Column       | Type       | Description                     |
| ------------ | ---------- | ------------------------------- |
| id           | UUID (PK)  | Primary key                     |
| document_id  | UUID (FK)  | Reference to uploaded_documents |
| element_type | String(50) | table, form, text, list_item    |
| parent_id    | UUID (FK)  | Self-reference for hierarchy    |
| page_number  | Integer    | Page location                   |
| section_path | Text       | e.g., "Section 3.2 > Table 1"   |
| order_index  | Integer    | Position in document            |
| bounding_box | JSONB      | Coordinate data                 |
| content      | JSONB      | Extracted content               |
| created_at   | Timestamp  | Extraction timestamp            |

**Indexes:**

- `idx_doc_hierarchy`: (document_id, parent_id)
- `idx_doc_order`: (document_id, page_number, order_index)

#### Findings

**Table:** `findings`

| Column           | Type        | Description                     |
| ---------------- | ----------- | ------------------------------- |
| id               | UUID (PK)   | Primary key                     |
| document_id      | UUID (FK)   | Reference to uploaded_documents |
| element_id       | UUID (FK)   | Reference to document_elements  |
| error_id         | String(50)  | Unique error identifier         |
| iteration        | Integer     | Iteration number (1-5)          |
| severity         | String(20)  | critical, major, minor          |
| issue_type       | String(50)  | gap, inconsistency, etc.        |
| description      | Text        | Finding description             |
| evidence         | Text        | Supporting evidence             |
| regulation_ref   | String(100) | Citation                        |
| confidence_score | Float       | 0.0 - 1.0                       |
| model_agreement  | String(20)  | e.g., "3/3"                     |
| critique_summary | JSONB       | Critique trail                  |
| created_at       | Timestamp   | Finding timestamp               |

**Indexes:**

- `idx_finding_document`: (document_id)
- `idx_finding_error`: (error_id)

### Relationships

```mermaid
erDiagram
    COMPLIANCE_BODIES ||--o{ REGULATION_DOCUMENTS : has
    REGULATION_DOCUMENTS ||--o{ REGULATION_TEXTS : contains
    COMPLIANCE_BODIES ||--o{ UPLOADED_DOCUMENTS : analyzes
    UPLOADED_DOCUMENTS ||--o{ DOCUMENT_ELEMENTS : contains
    DOCUMENT_ELEMENTS ||--o{ DOCUMENT_ELEMENTS : parent_of
    UPLOADED_DOCUMENTS ||--o{ FINDINGS : has
    DOCUMENT_ELEMENTS ||--o{ FINDINGS : generates
```

### Indexing Strategy

**Vector Indexes (pgvector):**

- `regulation_texts.embedding`: GiST index for cosine similarity search
- Enables fast RAG retrieval with `<=>` operator

**B-Tree Indexes:**

- Foreign keys: Auto-indexed for joins
- `(document_id, page_number, order_index)`: Optimizes element ordering
- `error_id`: Fast finding lookups across iterations

**JSONB Indexes:**

- GIN indexes on metadata JSONB columns for key-based queries

---

## Configuration & Environment Setup

### Environment Variables Reference

**Location:** [.env](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/.env), [.env.example](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/.env.example)

#### GCP Configuration

```env
# Project and Location
GCP_PROJECT_ID=multimodal-analyzer
GCP_LOCATION=us-east5
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Model-Specific Regions
CLAUDE_REGION=global
LLAMA_REGION=us-east5
GEMINI_REGION=us-central1
GPT_OSS_REGION=global

# Document AI
DOCAI_LOCATION=us
DOCAI_LAYOUT_PROCESSOR_ID=32308c6036df50a2
DOCAI_FORM_PROCESSOR_ID=41a5705cc8b8eb56
```

#### Database Configuration

```env
# PostgreSQL (with asyncpg driver)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:6384/rag_analyzer

# Redis
REDIS_URL=redis://localhost:6383/0
```

#### Application Settings

```env
# Server
DEBUG=True
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
UPLOAD_DIR=/tmp/uploads

# Processing
MAX_WORKERS=3
EMBEDDING_BATCH_SIZE=10
```

### GCP Configuration Requirements

#### Required APIs

**Enable via gcloud:**

```bash
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
```

#### Service Account Permissions

Required IAM roles:

- `roles/documentai.apiUser`
- `roles/aiplatform.user`
- `roles/storage.objectViewer` (if using GCS)

**Create Service Account:**

```bash
gcloud iam service-accounts create multimodal-analyzer \
  --display-name="Multimodal Analyzer Service Account"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:multimodal-analyzer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:multimodal-analyzer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

**Generate Key:**

```bash
gcloud iam service-accounts keys create ~/doc-analyzer-key.json \
  --iam-account=multimodal-analyzer@PROJECT_ID.iam.gserviceaccount.com
```

#### Document AI Processor Setup

**Create Processors:**

```bash
# Layout Parser
gcloud documentai processors create \
  --location=us \
  --display-name="Layout Parser" \
  --type=LAYOUT_PARSER_PROCESSOR

# Form Parser
gcloud documentai processors create \
  --location=us \
  --display-name="Form Parser" \
  --type=FORM_PARSER_PROCESSOR
```

---

## Processing Configuration

### Model Selection Options

**Multi-Model vs Single-Model:**

```env
# Use all models for consensus (recommended)
USE_MULTI_MODEL=true

# Use only one model (faster, cheaper)
USE_MULTI_MODEL=false
PRIMARY_MODEL=llama-scout  # Options: llama-scout, gemini-flash, gpt-oss
```

**Best Practices:**

- **Production**: `USE_MULTI_MODEL=true` for highest confidence
- **Development/Testing**: `USE_MULTI_MODEL=false` for faster iteration
- **Cost Optimization**: Single model with critique system enabled

### Confidence Thresholds

```env
# Findings with score ≥ 0.95 are included as high confidence
HIGH_CONFIDENCE_THRESHOLD=0.95

# Findings with score 0.80-0.95 are included as medium confidence
MEDIUM_CONFIDENCE_THRESHOLD=0.80

# Findings below 0.80 are discarded
```

**Tuning Guidelines:**

- **Higher thresholds** (0.97+): More conservative, fewer false positives
- **Lower thresholds** (0.85): More findings, potential false positives
- **Current settings**: Balanced for production use

### Consensus Methods

```env
# Options: agreement, confidence, hybrid
CONSENSUS_METHOD=hybrid

# Minimum percentage of models that must agree (0.0-1.0)
MIN_MODEL_AGREEMENT=0.66  # Requires 2/3 models
```

| Method       | Formula                               | Use Case                                          |
| ------------ | ------------------------------------- | ------------------------------------------------- |
| `agreement`  | Simple percentage of agreeing models  | When models don't provide confidence scores       |
| `confidence` | Average of model-provided confidences | When using models with built-in scoring           |
| `hybrid`     | Weighted combination (default)        | Production use, balances agreement and confidence |

### Iterative Analysis Settings

```env
# Maximum number of analysis iterations
MAX_ITERATIONS=5

# Stop when high-confidence findings ≤ this threshold
CONVERGENCE_THRESHOLD=0  # 0 = perfect compliance required

# Stop when medium-confidence findings ≤ this threshold
MEDIUM_CONVERGENCE_THRESHOLD=10
```

**Convergence Logic:**

```python
# Stops when:
# 1. high_confidence_findings <= CONVERGENCE_THRESHOLD, AND
# 2. medium_confidence_findings <= MEDIUM_CONVERGENCE_THRESHOLD, OR
# 3. iterations >= MAX_ITERATIONS, OR
# 4. No improvement from previous iteration
```

### Critique System Configuration

```env
# Enable Proposer-Critic-Refiner workflow
ENABLE_CRITIQUE_SYSTEM=true

# Model for initial findings (Proposer)
PROPOSER_MODEL=gemini-flash

# Model for critique and validation (Critic)
CRITIC_MODEL=llama-scout

# Use critique even in single-model mode (self-critique)
USE_CRITIQUE_IN_SINGLE_MODEL=true
```

**Recommendation:** Keep critique enabled for all modes to reduce false positives.

---

## Deployment & Operations

### Docker-Based Local Development

**Prerequisites:**

- Docker 20.10+
- Docker Compose 2.0+

**Start Services:**

```bash
# Start PostgreSQL and Redis
docker compose up -d

# Verify services
docker compose ps

# View logs
docker compose logs -f
```

**Stop Services:**

```bash
docker compose down

# Remove volumes (clean slate)
docker compose down -v
```

### Service Dependencies

#### PostgreSQL Container

```yaml
Image: pgvector/pgvector:pg16
Container: rag_analyzer_postgres
Port: 6384:5432
Database: rag_analyzer
User: user
Password: password
```

**Health Check:**

```bash
docker exec -it rag_analyzer_postgres pg_isready -U user -d rag_analyzer
```

**Enable pgvector:**

```bash
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Redis Container

```yaml
Image: redis:7-alpine
Container: rag_analyzer_redis
Port: 6383:6379
```

**Health Check:**

```bash
docker exec -it rag_analyzer_redis redis-cli ping
# Expected: PONG
```

### Monitoring and Metrics

**Prometheus Endpoint:** `GET /metrics`

**Available Metrics:**

- Request count by endpoint
- Response times
- Error rates
- Database connection pool stats
- LLM API call latencies

**Future:** Grafana dashboards for visualization

### Logging Configuration

**Log Level:** Set via `LOG_LEVEL` environment variable

- `DEBUG`: Verbose, all operations
- `INFO`: Standard operational logs (default)
- `WARNING`: Only warnings and errors
- `ERROR`: Errors only

**Log Format:** Structured JSON logging via `python-json-logger`

**Log Locations:**

- **Console**: stdout/stderr
- **Future**: Cloud Logging (GCP)

**Example Log Entry:**

```json
{
  "timestamp": "2026-02-08T16:30:00Z",
  "level": "INFO",
  "logger": "app.services.llm_client",
  "message": "Multi-LLM analysis completed",
  "document_id": "uuid",
  "models_used": ["gemini-flash", "llama-scout", "gpt-oss"],
  "duration_ms": 2345
}
```

---

## Document Processing Capabilities

### Supported Formats

**Input Formats:**

- PDF (Portable Document Format)
- DOCX (Microsoft Word)

**Output Formats:**

- **DOCX**: Color-coded redrafts and reports
- **PDF**: Final compliance reports
- **JSON**: Structured data for programmatic access

### Extraction Features

**Document AI Capabilities:**

| Feature                    | Description                                 |
| -------------------------- | ------------------------------------------- |
| **Text Extraction**        | Plain text with font and style preservation |
| **Table Detection**        | Identifies tables with row/column structure |
| **Form Recognition**       | Key-value pairs and form fields             |
| **List Detection**         | Bullets and numbered lists                  |
| **Hierarchical Structure** | Sections, subsections, and nesting          |
| **Coordinate Tracking**    | Bounding boxes for each element             |

### Structure Preservation

**Hierarchical Numbering:**

- **CARF**: `1.L.1.b.(4)` - Hierarchical with letters and numbers
- **MHRS/DBH**: `§3409.4(a)` - Legal-style section numbering

**Element Hierarchy:**

```
Document
├── Section 1
│   ├── Section 1.1
│   │   ├── Table 1.1.A
│   │   └── Paragraph
│   └── Section 1.2
└── Section 2
    └── Form
```

### Output Format Options

#### Color-Coded Redraft

**Colors:**

- **Black**: Original text (unchanged)
- **Blue**: Modified text (edits)
- **Red**: New additions

**Use Case:** Review and collaboration

#### Clean Redraft

**Format:** Standard document without markup  
**Use Case:** Final deliverable to stakeholders

#### Compliance Report

**Structure:**

1. **Summary**: Overview of findings by standard section
2. **Detailed Analysis**: Section-by-section breakdown with:
   - Regulation text (black)
   - Identified gaps (red)
   - Remediation suggestions (blue)

---

## Development Workflow

### Setup Instructions

**1. Clone Repository**

```bash
git clone <repository-url>
cd multimodal-analyzer
```

**2. Create Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure Environment**

```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

**5. Start Services**

```bash
docker compose up -d
```

**6. Enable pgvector**

```bash
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**7. Run Migrations**

```bash
alembic upgrade head
```

**8. Seed Compliance Bodies**

```bash
python scripts/seed_compliance_bodies.py
```

**9. Start Application**

```bash
uvicorn app.main:app --reload --port 8000
```

**10. Access APIs**

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Migrations

**Alembic Configuration:** [alembic.ini](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/alembic.ini)

**Create Migration:**

```bash
alembic revision --autogenerate -m "description of changes"
```

**Apply Migrations:**

```bash
alembic upgrade head
```

**Rollback:**

```bash
alembic downgrade -1  # Rollback one version
```

**View History:**

```bash
alembic history
alembic current
```

### Testing Approach

**Test Directory:** [tests/](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/tests/)

**Run Tests:**

```bash
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_analysis.py
```

**Test Categories:**

- Unit tests: Individual functions and classes
- Integration tests: Database and external API interactions
- End-to-end tests: Full workflow testing

### Best Practices

**Code Organization:**

- **Models**: Database models in `app/models/`
- **Schemas**: Pydantic schemas in `app/schemas/`
- **Services**: Business logic in `app/services/`
- **API Routes**: Endpoints in `app/api/`
- **Utilities**: Helper functions in `app/utils/`

**Async Patterns:**

- Use `async/await` for all I/O operations
- Database queries: `AsyncSession`
- LLM calls: `asyncio.gather()` for parallelism

**Error Handling:**

- Use try/except with specific exception types
- Log errors with context
- Return meaningful error responses

**Configuration:**

- All configurable values in environment variables
- Use `pydantic-settings` for type-safe configuration
- Never commit secrets to version control

---

## Appendix

### Useful Commands

**Database:**

```bash
# Connect to PostgreSQL
docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer

# Check tables
\dt

# View schema
\d table_name
```

**Redis:**

```bash
# Connect to Redis
docker exec -it rag_analyzer_redis redis-cli

# List keys
KEYS *

# Get value
GET key_name
```

**Application:**

```bash
# Run in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check logs
tail -f logs/app.log
```

### Reference Documentation

**Project Files:**

- [README.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/README.md) - Quick start guide
- [SYSTEM_ARCHITECTURE.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/SYSTEM_ARCHITECTURE.md) - Architecture overview
- [RAG_IMPLEMENTATION_PLAN.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/RAG_IMPLEMENTATION_PLAN.md) - Detailed implementation plan
- [QUICKSTART.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/QUICKSTART.md) - Quick start guide
- [QUICK_START.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/QUICK_START.md) - Alternative quick start
- [commands.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/commands.md) - Common commands

**External Documentation:**

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [LangChain](https://python.langchain.com/)
- [Google Document AI](https://cloud.google.com/document-ai/docs)
- [Vertex AI](https://cloud.google.com/vertex-ai/docs)

---

**Document Version:** 1.0.0  
**Generated:** February 8, 2026  
**Maintained By:** Development Team  
**For:** Product Team Reference
