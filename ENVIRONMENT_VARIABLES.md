# Environment Variables Documentation

This document provides a comprehensive reference for all environment variables used in the multimodal-analyzer system, with a focus on how they affect the compliance analysis process.

---

## Table of Contents

1. [GCP Infrastructure Configuration](#gcp-infrastructure-configuration)
2. [Model Configuration](#model-configuration)
3. [Document AI Configuration](#document-ai-configuration)
4. [Database & Cache Configuration](#database--cache-configuration)
5. [Application Settings](#application-settings)
6. [File Upload Settings](#file-upload-settings)
7. [Processing Settings](#processing-settings)
8. [Analysis Configuration](#analysis-configuration)
   - [Model Selection](#model-selection)
   - [Confidence Scoring](#confidence-scoring)
   - [Consensus Calculation](#consensus-calculation)
   - [Iterative Refinement](#iterative-refinement)
   - [Critique System](#critique-system)

---

## GCP Infrastructure Configuration

### `GCP_PROJECT_ID`

- **Description**: Google Cloud Platform project identifier
- **Range**: Any valid GCP project ID string
- **Current Value**: `multimodal-analyzer`
- **Effect on System**:
  - Used to initialize all GCP services (Vertex AI, Document AI)
  - Required for authentication and billing
  - **Critical**: System will not start without this

### `GCP_LOCATION`

- **Description**: Default GCP region for services
- **Range**: Any valid GCP region (e.g., `us-central1`, `us-east5`, `europe-west1`)
- **Current Value**: `us-east5`
- **Effect on System**:
  - Default location for GCP resources
  - Can be overridden by model-specific region settings
  - Affects latency and data residency

### `GOOGLE_APPLICATION_CREDENTIALS`

- **Description**: Path to GCP service account key file
- **Range**: Absolute file path to a valid JSON key file
- **Current Value**: `/home/oluwaseyi/doc-analyzer-key.json`
- **Effect on System**:
  - Required for authenticating with all GCP services
  - Must have permissions for Vertex AI, Document AI, and Cloud Storage
  - **Critical**: System will fail to authenticate without this

---

## Model Configuration

> [!IMPORTANT]
> Model regions must be set correctly based on where each model is available in Vertex AI Model Garden. Incorrect regions will cause model verification failures.

### `CLAUDE_REGION`

- **Description**: GCP region for Claude models (via Anthropic Vertex API)
- **Range**: `global`, `us-central1`, `us-east5`, `europe-west1`, etc.
- **Current Value**: `global`
- **Effect on Analysis**:
  - Determines where Claude API calls are routed
  - `global` enables automatic routing to nearest available region
  - Incorrect region causes Claude model to fail verification

### `LLAMA_REGION`

- **Description**: GCP region for Llama Scout model
- **Range**: Valid GCP regions where Llama models are deployed
- **Current Value**: `us-east5`
- **Effect on Analysis**:
  - Specifies where Llama Scout model is deployed
  - Must match actual deployment region in Model Garden
  - Affects model availability and latency

### `GEMINI_REGION`

- **Description**: GCP region for Gemini models
- **Range**: Valid GCP regions (typically `us-central1` for Gemini 2.0)
- **Current Value**: `us-central1`
- **Effect on Analysis**:
  - Gemini 2.0 Flash is optimized for RAG in `us-central1`
  - Different regions may have different model versions available

### `GPT_OSS_REGION`

- **Description**: GCP region for GPT-OSS models
- **Range**: `global` or specific GCP regions
- **Current Value**: `global`
- **Effect on Analysis**:
  - Similar to Claude, `global` enables automatic routing
  - Required for GPT-OSS model verification

---

## Document AI Configuration

### `DOCAI_LOCATION`

- **Description**: Document AI processor location
- **Range**: `us`, `eu`, or specific regions
- **Current Value**: `us`
- **Effect on Analysis**:
  - Determines data processing region for compliance
  - Affects Document AI OCR latency
  - Must match processor location during creation

### `DOCAI_LAYOUT_PROCESSOR_ID`

- **Description**: Document AI Layout Parser processor ID
- **Range**: Processor ID string from Document AI console
- **Current Value**: `bc2267d6f6cafc5`
- **Effect on Analysis**:
  - **Critical for document extraction**
  - Extracts document structure, paragraphs, tables, and layout
  - Wrong ID causes document processing to fail
  - Alternative: `32308c6036df50a2` (commented out)

### `DOCAI_FORM_PROCESSOR_ID`

- **Description**: Document AI Form Parser processor ID
- **Range**: Processor ID string from Document AI console
- **Current Value**: `41a5705cc8b8eb56`
- **Effect on Analysis**:
  - Used for extracting form fields and key-value pairs
  - Enhances analysis of structured documents
  - Optional but recommended for policy documents

---

## Database & Cache Configuration

### `DATABASE_URL`

- **Description**: PostgreSQL connection string with asyncpg driver
- **Range**: Valid PostgreSQL connection URL format
- **Current Value**: `postgresql+asyncpg://user:password@localhost:6384/rag_analyzer`
- **Effect on System**:
  - Stores all analysis results, findings, and document metadata
  - Async driver required for FastAPI performance
  - Database migrations managed via Alembic

### `REDIS_URL`

- **Description**: Redis connection string for caching and job queues
- **Range**: Valid Redis URL format
- **Current Value**: `redis://localhost:6383/0`
- **Effect on System**:
  - Caches regulation embeddings and frequent queries
  - Manages background job queues
  - Improves performance by reducing redundant LLM calls

---

## Application Settings

### `DEBUG`

- **Description**: Enable debug mode for development
- **Range**: `True` or `False`
- **Current Value**: `True`
- **Effect on System**:
  - Enables verbose logging and stack traces
  - Should be `False` in production for security
  - Affects log verbosity throughout the system

### `LOG_LEVEL`

- **Description**: Logging verbosity level
- **Range**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Current Value**: `INFO`
- **Effect on System**:
  - Controls amount of log output
  - `INFO` provides good balance for monitoring analysis progress
  - `DEBUG` useful for troubleshooting but very verbose

### `API_HOST`

- **Description**: API server bind address
- **Range**: IP address or `0.0.0.0` for all interfaces
- **Current Value**: `0.0.0.0`
- **Effect on System**:
  - `0.0.0.0` allows external connections
  - `127.0.0.1` restricts to localhost only

### `API_PORT`

- **Description**: API server port
- **Range**: 1-65535 (typically 8000-9000)
- **Current Value**: `8000`
- **Effect on System**:
  - Must not conflict with other services
  - Client applications must connect to this port

---

## File Upload Settings

### `MAX_UPLOAD_SIZE`

- **Description**: Maximum file upload size in bytes
- **Range**: Any positive integer (bytes)
- **Current Value**: `52428800` (50 MB)
- **Effect on Analysis**:
  - Files larger than this will be rejected
  - Affects which PDFs/DOCX files can be analyzed
  - Consider Document AI and memory limits when increasing

### `UPLOAD_DIR`

- **Description**: Directory for temporary file storage
- **Range**: Any valid directory path
- **Current Value**: `/tmp/uploads`
- **Effect on System**:
  - Stores uploaded documents during processing
  - Must have write permissions
  - Files cleaned up after analysis

---

## Processing Settings

### `MAX_WORKERS`

- **Description**: Maximum parallel workers for processing
- **Range**: 1-10 (depends on system resources)
- **Current Value**: `3`
- **Effect on Analysis**:
  - Controls parallelism for multi-element documents
  - Higher values = faster but more resource intensive
  - Limited by GCP API rate limits and memory

### `EMBEDDING_BATCH_SIZE`

- **Description**: Batch size for embedding generation
- **Range**: 1-100 (optimal: 10-50)
- **Current Value**: `10`
- **Effect on Analysis**:
  - Affects speed of regulation retrieval
  - Larger batches = more efficient but higher memory
  - Vertex AI embedding API has batch limits

---

## Analysis Configuration

This section covers variables that directly affect the compliance analysis behavior, quality, and convergence.

---

## Model Selection

### `USE_MULTI_MODEL`

- **Description**: Enable multi-LLM analysis for consensus
- **Range**: `true` or `false`
- **Current Value**: `true`
- **Effect on Analysis**:
  - **Critical configuration choice**
  - `true`: Uses all verified models (llama-scout, gemini-flash, gpt-oss) for consensus voting
  - `false`: Uses only `PRIMARY_MODEL` for single-LLM analysis
  - Multi-model provides higher confidence through agreement
  - Single-model is faster and cheaper but less robust
  - When `false`, critique system can still run if `USE_CRITIQUE_IN_SINGLE_MODEL=true`

### `PRIMARY_MODEL`

- **Description**: Which model to use when `USE_MULTI_MODEL=false`
- **Range**: `llama-scout`, `gemini-flash`, or `gpt-oss`
- **Current Value**: `gemini-flash`
- **Effect on Analysis**:
  - Only used when `USE_MULTI_MODEL=false`
  - Determines the single model for analysis
  - Gemini Flash recommended for speed/accuracy balance
  - Model must be successfully verified at startup

---

## Confidence Scoring

> [!IMPORTANT]
> Confidence thresholds are the primary controls for analysis strictness. Higher thresholds produce fewer but more reliable findings.

### `HIGH_CONFIDENCE_THRESHOLD`

- **Description**: Minimum score to classify a finding as high-confidence
- **Range**: `0.0` to `1.0` (recommended: `0.85` - `0.95`)
- **Current Value**: `0.90`
- **Effect on Analysis**:
  - **Critical impact on analysis results**
  - High-confidence findings are definite compliance violations
  - Higher threshold = stricter = fewer high-confidence findings
  - Lower threshold = more lenient = more high-confidence findings
  - Affects convergence criteria (see `CONVERGENCE_THRESHOLD`)
  - Recommended values:
    - `0.95`: Very strict, extremely reliable findings only
    - `0.90`: Balanced (current setting)
    - `0.85`: More inclusive, catches borderline issues

### `MEDIUM_CONFIDENCE_THRESHOLD`

- **Description**: Minimum score to classify a finding as medium-confidence
- **Range**: `0.0` to `HIGH_CONFIDENCE_THRESHOLD` (recommended: `0.70` - `0.85`)
- **Current Value**: `0.75`
- **Effect on Analysis**:
  - Medium-confidence findings are potential issues requiring review
  - Findings below this threshold are discarded
  - Gap between medium and high thresholds creates three tiers:
    1. High-confidence (≥ 0.90): Definite violations
    2. Medium-confidence (0.75-0.89): Possible violations
    3. Low-confidence (< 0.75): Discarded
  - Affects convergence criteria (see `MEDIUM_CONVERGENCE_THRESHOLD`)
  - Recommended values:
    - `0.80`: Cautious, fewer medium findings
    - `0.75`: Balanced (current setting)
    - `0.70`: Inclusive, catches more possibilities

---

## Consensus Calculation

### `CONSENSUS_METHOD`

- **Description**: Method for calculating confidence scores from multi-LLM outputs
- **Range**: `agreement`, `confidence`, or `hybrid`
- **Current Value**: `hybrid`
- **Effect on Analysis**:
  - **Controls how consensus confidence is computed**
  - **`agreement`** (Agreement-based scoring):
    - 70% weight on how many models agree
    - 15% grounding in source document
    - 10% regulation citation quality
    - 5% semantic consistency
    - Best when models have varying quality
  - **`confidence`** (Individual confidence-based):
    - 60% weight on individual model confidence scores
    - 20% grounding in source document
    - 10% regulation citation quality
    - 10% semantic consistency
    - Best when models provide reliable self-assessment
  - **`hybrid`** (Balanced - RECOMMENDED):
    - 35% model agreement
    - 25% individual model confidence
    - 25% grounding in source document
    - 10% regulation citation quality
    - 5% semantic consistency
    - Best overall approach combining multiple signals

### `MIN_MODEL_AGREEMENT`

- **Description**: Minimum fraction of models that must agree for clustering
- **Range**: `0.0` to `1.0` (recommended: `0.50` - `0.75`)
- **Current Value**: `0.66` (2 out of 3 models)
- **Effect on Analysis**:
  - Used in DBSCAN clustering to group similar findings
  - Higher value = stricter clustering = fewer consensus findings
  - With 3 models:
    - `0.66` requires 2/3 models to agree (current)
    - `0.50` allows simple majority
    - `1.00` requires all models to agree (very strict)
  - Affects the "model agreement" component of confidence scoring

---

## Iterative Refinement

> [!WARNING]
> Convergence thresholds control when analysis stops. Setting both to 0 means the document must be **perfectly compliant** before convergence, which may be impossible for some documents.

### `MAX_ITERATIONS`

- **Description**: Maximum number of analysis-redraft cycles
- **Range**: `1` to `10` (recommended: `3` - `5`)
- **Current Value**: `5`
- **Effect on Analysis**:
  - **Controls maximum refinement cycles**
  - Each iteration:
    1. Analyzes current document
    2. Generates redraft addressing findings
    3. Re-analyzes redraft
  - More iterations = more opportunities to reach compliance but slower and costlier
  - Analysis stops early if convergence thresholds are met
  - With `MAX_ITERATIONS=5`:
    - Fast documents may converge in 1-2 iterations
    - Complex documents use all 5 iterations
  - Cost consideration: Each iteration = full LLM analysis cycle

### `CONVERGENCE_THRESHOLD`

- **Description**: Maximum high-confidence findings to consider document converged
- **Range**: `0` to `50` (common: `0`, `3`, `5`)
- **Current Value**: `0`
- **Effect on Analysis**:
  - **Critical convergence criteria**
  - Document converges when BOTH conditions met:
    - High-confidence findings ≤ `CONVERGENCE_THRESHOLD`
    - Medium-confidence findings ≤ `MEDIUM_CONVERGENCE_THRESHOLD`
  - **`0`** (current): Document must have **zero** high-confidence violations
    - Strictest setting
    - Forces iterative refinement until perfect compliance or max iterations
    - May be impossible for some documents
  - **`3`**: Allows up to 3 minor high-confidence issues
    - More practical for real-world documents
  - **`5`**: Relaxed convergence
    - Useful for quick validation runs
  - Set to higher value to allow early stopping

### `MEDIUM_CONVERGENCE_THRESHOLD`

- **Description**: Maximum medium-confidence findings to consider document converged
- **Range**: `0` to `100` (common: `0`, `5`, `10`)
- **Current Value**: `10`
- **Effect on Analysis**:
  - **Secondary convergence criteria**
  - Works in conjunction with `CONVERGENCE_THRESHOLD`
  - Both thresholds must be satisfied for convergence
  - **`10`** (current): Allows up to 10 medium-confidence potential issues
    - Reasonable for complex documents
    - Medium findings often require human review anyway
  - **`0`**: Perfect compliance required (very strict)
  - **`20`**: Very relaxed, focuses on high-confidence issues only
  - Higher values allow faster convergence but may miss issues

#### Convergence Examples

| High Threshold | Medium Threshold | Behavior                                             |
| -------------- | ---------------- | ---------------------------------------------------- |
| `0`            | `0`              | Perfect compliance required (strictest)              |
| `0`            | `10`             | No high-confidence issues, up to 10 medium (current) |
| `3`            | `10`             | Up to 3 high, 10 medium (balanced)                   |
| `5`            | `20`             | Relaxed convergence (faster)                         |

---

## Critique System

> [!TIP]
> The critique system adds a second-pass validation layer. Enable it for higher quality analysis at the cost of additional LLM calls.

### `ENABLE_CRITIQUE_SYSTEM`

- **Description**: Enable Proposer → Critic → Refiner workflow
- **Range**: `true` or `false`
- **Current Value**: `true`
- **Effect on Analysis**:
  - **Major quality enhancement**
  - When `true`:
    1. **Proposer** model generates initial findings
    2. **Critic** model validates each finding
    3. **Refiner** adjusts confidence based on critique
  - Critique detects:
    - Hallucinations (unfounded claims)
    - Weak evidence
    - Incorrect regulation citations
    - Logical inconsistencies
  - Adjusts confidence scores up/down by ±0.2
  - Cost: ~2x LLM calls per analysis
  - Quality improvement: Significant reduction in false positives
  - When `false`: Skips critique, faster but less validated

### `PROPOSER_MODEL`

- **Description**: Which model generates initial findings in critique workflow
- **Range**: `llama-scout`, `gemini-flash`, or `gpt-oss`
- **Current Value**: `gemini-flash`
- **Effect on Analysis**:
  - Only used when `ENABLE_CRITIQUE_SYSTEM=true`
  - Initial findings come from this model
  - Gemini Flash recommended for speed
  - Different from `PRIMARY_MODEL` (used for single-model mode)

### `CRITIC_MODEL`

- **Description**: Which model critiques the proposer's findings
- **Range**: `llama-scout`, `gemini-flash`, or `gpt-oss`
- **Current Value**: `llama-scout`
- **Effect on Analysis**:
  - Only used when `ENABLE_CRITIQUE_SYSTEM=true`
  - **Should be different from `PROPOSER_MODEL`** for diversity
  - Validates proposer findings with fresh perspective
  - Llama Scout good for critique due to structured reasoning
  - If same as proposer, system automatically selects different model

### `USE_CRITIQUE_IN_SINGLE_MODEL`

- **Description**: Enable critique even when `USE_MULTI_MODEL=false`
- **Range**: `true` or `false`
- **Current Value**: `true`
- **Effect on Analysis**:
  - Only relevant when `USE_MULTI_MODEL=false`
  - When both `false`: Single model, no critique (fastest, cheapest, lowest quality)
  - When `USE_MULTI_MODEL=false` but `USE_CRITIQUE_IN_SINGLE_MODEL=true`:
    - Single model generates findings
    - Critique system validates findings
    - Good balance of speed and quality
  - Recommended: Keep `true` for better results even in single-model mode

---

## Configuration Scenarios

### Fastest Analysis (Low Cost)

```
USE_MULTI_MODEL=false
PRIMARY_MODEL=gemini-flash
ENABLE_CRITIQUE_SYSTEM=false
MAX_ITERATIONS=1
```

- Single model, no critique, no iterations
- Fastest and cheapest
- Lower confidence in results

### Balanced Analysis (Recommended)

```
USE_MULTI_MODEL=true
ENABLE_CRITIQUE_SYSTEM=true
HIGH_CONFIDENCE_THRESHOLD=0.90
MEDIUM_CONFIDENCE_THRESHOLD=0.75
CONVERGENCE_THRESHOLD=0
MEDIUM_CONVERGENCE_THRESHOLD=10
MAX_ITERATIONS=5
CONSENSUS_METHOD=hybrid
```

- Multi-model consensus with critique
- Iterative refinement until compliant
- Current configuration

### Highest Quality (High Cost)

```
USE_MULTI_MODEL=true
ENABLE_CRITIQUE_SYSTEM=true
HIGH_CONFIDENCE_THRESHOLD=0.95
MEDIUM_CONFIDENCE_THRESHOLD=0.80
CONVERGENCE_THRESHOLD=0
MEDIUM_CONVERGENCE_THRESHOLD=0
MAX_ITERATIONS=5
CONSENSUS_METHOD=hybrid
MIN_MODEL_AGREEMENT=1.0
```

- Strictest thresholds
- All models must agree
- Perfect compliance required
- Most expensive and slowest

### Quick Validation

```
USE_MULTI_MODEL=true
ENABLE_CRITIQUE_SYSTEM=true
CONVERGENCE_THRESHOLD=5
MEDIUM_CONVERGENCE_THRESHOLD=20
MAX_ITERATIONS=3
```

- Multi-model for reliability
- Relaxed convergence for speed
- Good for initial assessment

---

## Environment Variable Dependencies

```mermaid
graph TD
    A[USE_MULTI_MODEL] -->|false| B[PRIMARY_MODEL]
    A -->|false| C[USE_CRITIQUE_IN_SINGLE_MODEL]
    A -->|true| D[All Available Models]

    E[ENABLE_CRITIQUE_SYSTEM] -->|true| F[PROPOSER_MODEL]
    E -->|true| G[CRITIC_MODEL]

    H[Consensus Calculation] --> I[CONSENSUS_METHOD]
    H --> J[MIN_MODEL_AGREEMENT]
    H --> K[HIGH_CONFIDENCE_THRESHOLD]
    H --> L[MEDIUM_CONFIDENCE_THRESHOLD]

    M[Iterative Refinement] --> N[MAX_ITERATIONS]
    M --> O[CONVERGENCE_THRESHOLD]
    M --> P[MEDIUM_CONVERGENCE_THRESHOLD]

    O --> K
    P --> L

    style A fill:#ffcccc
    style E fill:#ccffcc
    style K fill:#ccccff
    style L fill:#ccccff
```

---

## Cost Implications

Variables with significant cost impact:

1. **`USE_MULTI_MODEL`**: 3x LLM calls vs 1x
2. **`ENABLE_CRITIQUE_SYSTEM`**: 2x additional LLM calls
3. **`MAX_ITERATIONS`**: Multiplies all LLM costs by iterations
4. **`CONVERGENCE_THRESHOLD` / `MEDIUM_CONVERGENCE_THRESHOLD`**: Lower values = more iterations = higher cost

**Example Cost Analysis:**

- Single-model, no critique, 1 iteration: **1x baseline**
- Multi-model, with critique, 1 iteration: **6x baseline** (3 models × 2 critique passes)
- Multi-model, with critique, 5 iterations: **30x baseline** (worst case)

See [COST_ANALYSIS.md](file:///home/oluwaseyi/dev247/official/multimodal-analyzer/COST_ANALYSIS.md) for detailed cost breakdowns.

---

## Recommended Tuning Process

1. **Start with defaults** (current `.env` settings)
2. **Run sample analysis** and review findings quality
3. **Adjust thresholds** based on results:
   - Too many false positives → Increase `HIGH_CONFIDENCE_THRESHOLD`
   - Missing issues → Decrease `MEDIUM_CONFIDENCE_THRESHOLD`
4. **Tune convergence** for your use case:
   - Strict compliance → Keep `CONVERGENCE_THRESHOLD=0`
   - Faster validation → Increase thresholds
5. **Monitor costs** and adjust `MAX_ITERATIONS` if needed

---

## Troubleshooting

### Analysis won't converge

- **Issue**: All 5 iterations used, still finding violations
- **Solutions**:
  - Increase `CONVERGENCE_THRESHOLD` or `MEDIUM_CONVERGENCE_THRESHOLD`
  - Review document quality - may have genuine compliance issues
  - Check if thresholds are too strict for document type

### Too many false positives

- **Issue**: High-confidence findings that aren't real violations
- **Solutions**:
  - Increase `HIGH_CONFIDENCE_THRESHOLD` (try `0.95`)
  - Enable critique: `ENABLE_CRITIQUE_SYSTEM=true`
  - Switch consensus method: `CONSENSUS_METHOD=agreement`

### Missing compliance issues

- **Issue**: Known violations not detected
- **Solutions**:
  - Decrease `MEDIUM_CONFIDENCE_THRESHOLD` (try `0.70`)
  - Use multi-model: `USE_MULTI_MODEL=true`
  - Check regulation database has relevant regulations

### High API costs

- **Issue**: Analysis is too expensive
- **Solutions**:
  - Reduce `MAX_ITERATIONS` (try `3`)
  - Use single model: `USE_MULTI_MODEL=false`
  - Disable critique: `ENABLE_CRITIQUE_SYSTEM=false`
  - Increase convergence thresholds for faster stopping

