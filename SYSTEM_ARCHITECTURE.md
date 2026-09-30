# High-Performance Multi-LLM RAG Analysis Service - System Architecture

This document provides a comprehensive overview of the end-to-end system design, integrating extraction, orchestration, multi-LLM consensus, and localized output generation.

## 1. High-Level Flow Diagram

```mermaid
graph TB
    subgraph "User Layer"
        U[Client App / Postman]
    end

    subgraph "API Layer (FastAPI)"
        API[REST Endpoints]
        REG_API[POST /api/regulations/upload]
        ANALYZE_API[POST /api/documents/analyze]
        RESULT_API[GET /api/documents/id/result]
        REDRAFT_API[GET /api/documents/id/redraft]
    end

    subgraph "Extraction Layer (GCP)"
        DAI[Document AI Layout Parser]
        PARSER[ComplianceBodySectionParser]
    end

    subgraph "Orchestration Layer (LangGraph)"
        LG[LangGraph State Machine]
        ROUTER[Element Router Agent]
        AGENTS[Specialized Agents<br/>Table, Form, List, Text]
    end

    subgraph "AI Processing Layer (Vertex AI)"
        MODELS[Multi-LLM Pool<br/>Gemini 2.5, Claude 4.5, Llama 4]
        CE[Consensus Engine]
        SCORE[Confidence Scoring<br/>Agreement + Grounding]
    end

    subgraph "Synthesis & Verification"
        D_REDRAFT[Dual Redrafting<br/>Gemini vs Claude]
        PASS_VERIFY[Multi-Pass Verifier]
    end

    subgraph "Storage & Queue"
        DB[(PostgreSQL + pgvector)]
        REDIS[(Redis Cache / Queue)]
        CELERY[Celery Workers]
    end

    U --> API
    API --> DAI
    DAI --> PARSER
    PARSER --> DB

    API --> CELERY
    CELERY --> LG
    LG --> ROUTER
    ROUTER --> AGENTS
    AGENTS --> MODELS
    MODELS --> CE
    CE --> SCORE
    SCORE --> D_REDRAFT
    D_REDRAFT --> PASS_VERIFY
    PASS_VERIFY --> DB

    REDIS -.-> MODELS
```

## 2. Component Breakdown

### A. Extraction Layer (Google Document AI)

- **Layout Parser**: Identifies semantics (tables, sections, forms).
- **Coordinate Mapping**: Preserves `boundingPoly` and `normalizedVertices` for visual grounding.
- **Structural Parser**: Uses regex-based logic to handle Standard/Legal (MHRS) vs. Hierarchical (CARF) numbering.

### B. Orchestration Layer (LangGraph)

- **Stateful Memory**: Tracks element processing, intermediate findings, and consensus status.
- **Element Routing**: Dynamically assigns sub-tasks to agents specialized in tabular data, form logic, or narrative text.
- **Fault Tolerance**: Implements PostgreSQL checkpointers for job recovery.

### C. Multi-LLM Consensus Layer (Vertex AI Model Garden)

- **Diversity**: Parallel processing via **Gemini 2.5 Pro**, **Claude Opus 4.5**, and **Llama 4**.
- **Consensus Engine**: Semantic clustering of findings to eliminate hallucinations.
- **Confidence Formula**: Weighted score (50% Agreement, 30% Grounding, 10% Citation, 10% Consistency).
- **Threshold**: Strict $\ge 0.90$ for automated inclusion.

### D. Synthesis & Verification Layer

- **Dual Redrafting**: Generates compliant text using both Gemini and Claude, selecting based on a third-party "Quality Scorer" LLM.
- **Final Consensus**: A second round of multi-LLM verification on the finalized document to ensure zero drift.

## 3. API & Output Definitions

### Primary Endpoints

- `POST /api/regulations/upload`: Ingests reference manuals.
- `POST /api/documents/analyze`: Starts asynchronous document analysis.
- `GET /api/documents/{id}/result`: Returns structured JSON findings.
- `GET /api/documents/{id}/redraft`: Returns the enhanced document (Word/HTML/PDF).

### Color-Coded Redrafting (Default)

- **Black**: Unchanged original text.
- **Blue**: In-line modifications.
- **Red**: New insertions/entries.

### Analysis Report Structure (Default: DOCX)

- **PART 1: SUMMARY OF ANALYSIS**: Grouped findings by standard heading (e.g., "1.L. ACCESSIBILITY") with summaries of issues.
- **PART 2: DETAILED ANALYSIS BREAKDOWN**:
  - **Black**: Actual section text from standard manual.
  - **Red**: Identified gaps/issues.
  - **Blue**: Theraptly's suggested remediations.

## 4. Performance Metrics

- **Parallelism**: Asynchronous model inference across 3+ flagship LLMs.
- **Reliability**: Consensus matching reduces hallucination rates in regulatory contexts.
- **Traceability**: All claims linked to source coordinates in original PDF/DOCX.
