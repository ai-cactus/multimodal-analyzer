# High-Performance Multi-LLM Agentic RAG Analysis Service

Comprehensive implementation plan for a next-generation AI analysis service leveraging GCP Document AI, Vertex AI Model Garden, and LangGraph for maximum precision and reliability.

---

## System Goals

- **High-Fidelity Extraction**: Capture text, tables, forms, bullets, and numbering with complete structure preservation
- **Multi-LLM Consensus**: Validate findings across Gemini 2.5 Pro, Claude Opus 4.5, and Llama 4
- **Agentic Intelligence**: Element-specific processing with specialized agents
- **Maximum Confidence**: Aggressive filtering (≥0.90 threshold) with multi-pass verification
- **Human Oversight**: Final output review before delivery

---

## User-Facing Workflow

### 1. Regulation Manual Ingestion

- Admin uploads compliance manuals (MHRS, CARF, DBH) via API
- System extracts, chunks, and embeds regulations for retrieval
- One canonical manual per compliance body

### 2. Document Analysis Request

- User uploads policy document via API
- Specifies compliance body and optional section
- System processes asynchronously

### 3. Results Retrieval

- **Analysis Result** (JSON): Programmatic access to findings
- **Analysis Report** (PDF/DOCX/TXT): Human-readable compliance report
- **Redraft** (DOCX/HTML/PDF/JSON): Color-coded or clean version

---

## REST API Specification

### Regulation Management

#### **POST /api/regulations/upload**

Upload a compliance manual for a specific body.

**Request**:

```json
{
  "compliance_body": "MHRS|CARF|DBH",
  "file": "<multipart/form-data>",
  "version": "2025",
  "effective_date": "2025-01-01"
}
```

**Response**:

```json
{
  "regulation_id": "uuid",
  "compliance_body": "MHRS",
  "status": "processing",
  "total_pages": 450,
  "estimated_completion": "2026-01-26T09:15:00Z"
}
```

**Process**:

1. Extract document using Document AI
2. Chunk by section (§3409, §3411, etc.)
3. Generate embeddings (Vertex AI text-embedding-005)
4. Store in `RegulationDocument` and `RegulationText` tables

---

### Document Analysis

#### **POST /api/documents/analyze**

Submit a document for compliance analysis.

**Request**:

```json
{
  "file": "<multipart/form-data>",
  "compliance_body_id": 1, // Required
  "compliance_section": "§3409-3412", // Optional: null = entire manual
  "filename": "Complaint_Grievance_Policy.docx",
  "redraft_mode": "color_coded|clean|both", // Default: color_coded
  "output_formats": ["docx", "html", "pdf", "json"] // Default: ["docx"]
}
```

**Response**:

```json
{
  "document_id": "uuid",
  "status": "processing",
  "estimated_completion": "2026-01-26T09:20:00Z",
  "check_url": "/api/documents/{document_id}/status"
}
```

**Processing Steps**:

1. Extract with Document AI → `document_elements` table
2. Route to specialized agents
3. Run multi-LLM analysis
4. Execute consensus engine
5. Generate redraft (dual-model if requested)
6. Multi-LLM verification
7. Status → `completed`

---

#### **GET /api/documents/{id}/status**

Check processing status.

**Response**:

```json
{
  "document_id": "uuid",
  "status": "processing|completed|failed",
  "progress": {
    "current_step": "Multi-LLM Verification",
    "percent_complete": 85,
    "elements_processed": 45,
    "total_elements": 52
  },
  "estimated_completion": "2026-01-26T09:20:00Z"
}
```

---

#### **GET /api/documents/{id}/result**

Retrieve analysis result in JSON (programmatic access).

**Response**:

```json
{
  "document_id": "uuid",
  "status": "completed",
  "overall_compliance_score": 72.5,
  "high_confidence_findings": [
    {
      "finding_id": "uuid",
      "element_id": "uuid",
      "element_type": "table",
      "section_path": "Section 3 > Table 1",
      "page_number": 5,
      "severity": "critical",
      "issue_type": "gap",
      "description": "Table missing required 'Resolution Timeline' column",
      "evidence": "Table headers: Complaint ID, Date, Type, Status",
      "regulation_ref": "§3409.4(a)",
      "confidence_score": 0.95,
      "model_agreement": "3/3"
    }
  ],
  "medium_confidence_findings": [...],
  "total_findings": 12,
  "critical_count": 3,
  "major_count": 6,
  "minor_count": 3
}
```

---

#### **GET /api/documents/{id}/report**

Generate human-readable compliance report.

**Query Parameters**:

- `format`: `pdf|docx|txt` (default: `docx`)

**Response**: Binary file download

**Report Structure**:

```
COMPLIANCE ANALYSIS REPORT
==========================
Document: Complaint_Grievance_Policy.docx
Compliance Body: CARF 2025 BH Standards
Analysis Date: 2026-01-27
Overall Compliance Score: 87.5%

PART 1: SUMMARY OF ANALYSIS
---------------------------
### SECTION 1.L. ACCESSIBILITY
**Description**:
[AI-Generated description of the section from the standard manual]

**Key Areas Addressed**:
- [Point 1]
- [Point 2]
- [AI-Generated key areas addressed by this section]

**Recommendations**:
- [List of Related Sections: 1.L.1.b.(4), 1.L.1.b.(7)]
  *Summary of Issues*: [AI-Generated summary of gaps for this group of sections]

- [List of Related Sections: 1.L.2.b.(1), 1.L.2.b.(2)]
  *Summary of Issues*: [AI-Generated summary of gaps for this group of sections]

PART 2: DETAILED ANALYSIS BREAKDOWN
-----------------------------------
*Detailed analysis breakdown containing issues based on each section in the Standard Manual the analyzed document failed to fulfill.*

#### 1.L.1.b.(4)
[BLACK TEXT] Actual Section from Standard Manual:
"{Actual text of section 1.L.1.b.(4) from CARF manual}"

[RED TEXT] Identified Gaps:
- Issue 1: [Specific gap found in user document]
- Issue 2: [Specific gap found in user document]

[BLUE TEXT] Theraptly's Suggestions:
[Specific remediation suggestions for this section]

#### 1.L.1.b.(7)
[BLACK TEXT] Actual Section from Standard Manual:
"{Actual text of section 1.L.1.b.(7) from CARF manual}"

[RED TEXT] Identified Gaps:
- [Issue description]

[BLUE TEXT] Theraptly's Suggestions:
[Re-drafting or modification suggestion]
```

---

#### **GET /api/documents/{id}/redraft**

Retrieve color-coded or clean redrafted document.

**Query Parameters**:

- `mode`: `color_coded|clean` (default: `color_coded`)
- `format`: `docx|html|pdf|json` (default: `docx`)

**Response**: Binary file download or JSON

**Color Coding Scheme**:

- **Black**: Unchanged original text
- **Blue**: In-place edits (modifications)
- **Red**: New additions/insertions

**Implementation (python-docx)**:

```python
from docx import Document
from docx.shared import RGBColor

def generate_color_coded_redraft(original_elements, findings, redrafted_text):
    """
    Generate DOCX with color-coded changes
    """
    doc = Document()

    # Color definitions
    COLOR_UNCHANGED = RGBColor(0, 0, 0)      # Black
    COLOR_MODIFIED = RGBColor(0, 0, 255)     # Blue
    COLOR_ADDITION = RGBColor(255, 0, 0)     # Red

    for element in original_elements:
        if element.id not in findings:
            # Unchanged: black text
            para = doc.add_paragraph(element.content)
            for run in para.runs:
                run.font.color.rgb = COLOR_UNCHANGED
        else:
            finding = findings[element.id]

            if finding.change_type == 'modification':
                # Modified: blue text
                para = doc.add_paragraph(finding.redrafted_content)
                for run in para.runs:
                    run.font.color.rgb = COLOR_MODIFIED

            elif finding.change_type == 'addition':
                # Addition: red text
                para = doc.add_paragraph(finding.redrafted_content)
                for run in para.runs:
                    run.font.color.rgb = COLOR_ADDITION

    return doc
```

**HTML Format** (for web preview):

```html
<div class="redraft-document">
  <p class="unchanged">This text remains the same.</p>
  <p class="modified">This text was edited for compliance.</p>
  <p class="addition">This is a new paragraph added for compliance.</p>
</div>

<style>
  .unchanged {
    color: black;
  }
  .modified {
    color: blue;
  }
  .addition {
    color: red;
  }
</style>
```

**JSON Format** (for custom rendering):

```json
{
  "elements": [
    {
      "element_id": "uuid",
      "type": "paragraph",
      "change_type": "unchanged|modified|addition",
      "original_content": "...",
      "redrafted_content": "...",
      "color_code": "black|blue|red"
    }
  ]
}
```

---

## Architecture Overview

### 1. Document Extraction Layer (Google Document AI)

**Technology**: Document AI Layout Parser + Form Parser

**Output Structure**:

```json
{
  "pages": [{
    "pageNumber": 1,
    "elements": [{
      "elementId": "uuid",
      "type": "table|form|text|list_item|numbering",
      "parentId": "uuid|null",
      "sectionPath": "Section 3.2 > Table 1",
      "orderIndex": 5,
      "boundingBox": {
        "vertices": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
        "normalizedVertices": [[nx1,ny1], ...]
      },
      "content": {...},
      "textAnchor": {"startIndex": 124, "endIndex": 456}
    }]
  }]
}
```

**Database Schema** (SQLAlchemy 2.0):

```python
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector
import uuid

class Base(DeclarativeBase):
    pass

class DocumentElement(Base):
    __tablename__ = 'document_elements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('uploaded_documents.id'), nullable=False)
    element_type = Column(String(50), nullable=False)  # 'text'|'table'|'form'|'list_item'|'numbering'
    parent_id = Column(UUID(as_uuid=True), ForeignKey('document_elements.id'), nullable=True)
    page_number = Column(Integer)
    section_path = Column(Text)
    order_index = Column(Integer)
    bounding_box = Column(JSONB)
    content = Column(JSONB)
    raw_docai_output = Column(JSONB)
    created_at = Column(TIMESTAMP)

    # Relationships
    document = relationship("UploadedDocument", back_populates="elements")
    children = relationship("DocumentElement", back_populates="parent")
    parent = relationship("DocumentElement", remote_side=[id], back_populates="children")

    __table_args__ = (
        Index('idx_doc_hierarchy', 'document_id', 'parent_id'),
        Index('idx_doc_order', 'document_id', 'page_number', 'order_index'),
    )

class RegulationText(Base):
    __tablename__ = 'regulation_texts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation_id = Column(UUID(as_uuid=True), ForeignKey('regulation_documents.id'))
    section_ref = Column(Text)  # '1.B.5.a.(2)(a)B.' or '§3405.1'
    text = Column(Text)
    embedding_v2 = Column(Vector(768))  # pgvector type
    created_at = Column(TIMESTAMP)
```

---

### 2. LangGraph Orchestration Layer

**State Schema**:

```python
from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph
import operator

class RAGAnalysisState(TypedDict):
    # Document structure
    document_id: str
    elements: List[DocumentElement]
    current_element_idx: int

    # Multi-LLM outputs
    llm_outputs: Annotated[Dict[str, List[Finding]], operator.add]

    # Consensus results
    claim_clusters: List[ClaimCluster]
    high_confidence_findings: List[Finding]  # score >= 0.90
    medium_confidence_findings: List[Finding]  # 0.70 <= score < 0.90

    # Synthesis
    redraft_candidates: Dict[str, str]  # {model_name: redrafted_text}
    selected_redraft: str
    final_report: str

    # Verification
    verification_scores: Dict[str, float]
    final_confidence: float

    # Control
    status: str  # 'extracting'|'analyzing'|'consensus'|'redrafting'|'verifying'|'review'|'complete'
    errors: Annotated[List[str], operator.add]
```

**Graph Flow**:

```
Extract → Route → [Table|Form|List|Text]Agent → Multi-LLM Analysis →
Consensus Engine → Dual Redrafting → Quality Selection →
Multi-LLM Verification → Human Review → Final Output
```

---

### 3. Specialized Agents

**Router Agent**:

```python
ELEMENT_TYPE_ROUTING = {
    'table': TableAnalysisAgent,
    'form': FormValidationAgent,
    'list_item': ListStructureAgent,
    'numbering': NumberingAnalysisAgent,
    'text': ContentAnalysisAgent
}
```

**Agent-Specific Prompts**:

```python
TABLE_ANALYSIS_PROMPT = """
You are analyzing a TABLE from a compliance document.

# Context
- Document: {document_name}
- Location: {section_path} (Page {page_number})
- Table structure: {num_rows} rows × {num_cols} columns
- Table content:
{table_markdown}

- Relevant regulations:
{regulations}

# Task
Analyze this table for:
1. Missing required data fields
2. Inconsistent values or formats
3. Non-compliant data ranges
4. Structural issues (missing headers, unclear hierarchy)

# Output Format (STRICT JSON)
{{
  "findings": [
    {{
      "claim_id": "uuid",
      "issue_type": "gap|inconsistency|non-compliance|structural",
      "severity": "critical|major|minor",
      "description": "detailed finding",
      "evidence": "specific cell or row reference",
      "regulation_ref": "citation"
    }}
  ]
}}
"""

FORM_ANALYSIS_PROMPT = """
Analyze this FORM for missing fields, invalid values, and compliance gaps...
[Similar structure]
"""

LIST_ANALYSIS_PROMPT = """
Analyze this LIST/BULLETS for completeness, ordering, and required items...
"""
```

---

### 4. Multi-LLM Processing

**Models**: Gemini 2.5 Pro, Claude Opus 4.5, Llama 4

**Execution**:

```python
async def run_multi_llm_analysis(element: DocumentElement, regulations: List[str]) -> Dict[str, List[Finding]]:
    """Run same prompt across all 3 models in parallel"""

    prompt = AGENT_PROMPTS[element.type].format(
        document_name=element.document_name,
        section_path=element.section_path,
        page_number=element.page_number,
        element_content=element.content,
        regulations=regulations
    )

    # Parallel execution with timeout
    tasks = [
        call_vertex_model("gemini-2.5-pro", prompt, schema=FindingSchema),
        call_vertex_model("claude-opus-4.5", prompt, schema=FindingSchema),
        call_vertex_model("llama-4", prompt, schema=FindingSchema)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "gemini": results[0],
        "claude": results[1],
        "llama": results[2]
    }
```

**Output Validation** (Pydantic):

```python
from pydantic import BaseModel, Field

class Finding(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: Literal["gap", "inconsistency", "non-compliance", "structural"]
    severity: Literal["critical", "major", "minor"]
    description: str
    evidence: str
    regulation_ref: str
```

---

### 5. Consensus & Confidence Engine

**Claim Matching Algorithm**:

```python
from sklearn.cluster import DBSCAN
import numpy as np

class ConsensusEngine:
    def __init__(self):
        self.embedding_service = VertexEmbeddingService()

    def create_claim_clusters(self, llm_outputs: Dict[str, List[Finding]]) -> List[ClaimCluster]:
        """
        1. Extract all findings from all models
        2. Generate embeddings for each finding.description
        3. Use DBSCAN clustering (eps=0.12) to group semantically similar claims
        4. Return clusters with metadata
        """
        all_findings = []
        for model, findings in llm_outputs.items():
            for finding in findings:
                all_findings.append({
                    'model': model,
                    'finding': finding,
                    'embedding': self.embedding_service.generate_embedding(
                        finding.description,
                        task_type="SEMANTIC_SIMILARITY"
                    )
                })

        embeddings_matrix = np.array([f['embedding'] for f in all_findings])

        # DBSCAN clustering
        clustering = DBSCAN(eps=0.12, min_samples=1, metric='cosine')
        labels = clustering.fit_predict(embeddings_matrix)

        # Group by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(all_findings[idx])

        return [ClaimCluster(findings_group) for findings_group in clusters.values()]
```

**Multi-Dimensional Confidence Scoring**:

```python
def calculate_confidence_score(cluster: ClaimCluster, source_element: DocumentElement) -> float:
    """
    Components:
    1. Agreement Score (A): # models agreeing / total models
    2. Grounding Score (G): % of claim text verifiable in source coordinates
    3. Regulation Strength (R): Quality of regulation citation
    4. Semantic Consistency (S): 1 - std(embeddings)

    Weights: A=50%, G=30%, R=10%, S=10%

    Thresholds (user requested "higher is better"):
    - C >= 0.90: High confidence (auto-include)
    - 0.70 <= C < 0.90: Medium confidence (include but flag)
    - C < 0.70: Low confidence (auto-exclude)
    """

    # Agreement: How many models reported this?
    agreement = len(cluster.models) / 3.0  # 3 total models

    # Grounding: Can we verify claim in original document?
    grounding = verify_claim_grounding(
        claim_text=cluster.representative_finding.description,
        source_coords=source_element.bounding_box,
        source_content=source_element.content
    )

    # Regulation strength: Is citation specific and valid?
    regulation_strength = score_regulation_citation(
        cluster.representative_finding.regulation_ref
    )

    # Semantic consistency: How similar are the embeddings?
    semantic_consistency = 1.0 - np.std([emb for emb in cluster.embeddings])

    confidence = (
        0.50 * agreement +
        0.30 * grounding +
        0.10 * regulation_strength +
        0.10 * semantic_consistency
    )

    return confidence

def verify_claim_grounding(claim_text: str, source_coords: dict, source_content: dict) -> float:
    """
    Extract key phrases from claim, check if they appear in source content
    Return ratio of verified phrases
    """
    key_phrases = extract_key_phrases(claim_text)
    verified = 0

    for phrase in key_phrases:
        if phrase.lower() in str(source_content).lower():
            verified += 1

    return verified / len(key_phrases) if key_phrases else 0.0
```

**Conflict Resolution**:

```python
def resolve_conflicts(cluster: ClaimCluster) -> Finding:
    """
    When models disagree on severity or recommendation:
    1. Severity: Take the highest (most conservative)
    2. Description: Use the most detailed version
    3. Evidence: Merge all unique evidence quotes
    """
    findings = cluster.findings

    # Most severe
    severity_order = {"critical": 3, "major": 2, "minor": 1}
    max_severity = max(findings, key=lambda f: severity_order[f.severity]).severity

    # Most detailed description
    best_description = max(findings, key=lambda f: len(f.description)).description

    # Merged evidence
    all_evidence = " | ".join(set([f.evidence for f in findings]))

    return Finding(
        severity=max_severity,
        description=best_description,
        evidence=all_evidence,
        regulation_ref=findings[0].regulation_ref  # All should be same
    )
```

---

### 6. Document Synthesis & Dual Redrafting

**Dual-Model Redrafting** (User requested: "Try both and pick best"):

```python
async def dual_model_redraft(high_confidence_findings: List[Finding], original_elements: List[DocumentElement]) -> str:
    """
    Generate redrafted document with BOTH Gemini 2.5 Pro and Claude Opus 4.5
    Then select the best output based on quality metrics
    """

    synthesis_prompt = """
You are creating a compliance-enhanced version of the original document.

# High-Confidence Findings (score >= 0.90)
{findings_json}

# Original Document Structure
{document_outline}

# Task
Create a redrafted document that:
1. Preserves original hierarchy (sections, tables, forms, lists)
2. Replaces non-compliant content with compliant alternatives
3. Maintains professional tone and original intent
4. Adds compliance citations where needed
5. Preserves all compliant content unchanged

# Output: Complete redrafted document in original format
"""

    # Run both models in parallel
    gemini_redraft, claude_redraft = await asyncio.gather(
        call_vertex_model("gemini-2.5-pro", synthesis_prompt, max_tokens=16000),
        call_vertex_model("claude-opus-4.5", synthesis_prompt, max_tokens=16000)
    )

    # Quality scoring
    gemini_score = await evaluate_redraft_quality(gemini_redraft, high_confidence_findings)
    claude_score = await evaluate_redraft_quality(claude_redraft, high_confidence_findings)

    # Select best
    selected = gemini_redraft if gemini_score > claude_score else claude_redraft
    selected_model = "gemini-2.5-pro" if gemini_score > claude_score else "claude-opus-4.5"

    logger.info(f"Dual redraft scores: Gemini={gemini_score:.3f}, Claude={claude_score:.3f}. Selected: {selected_model}")

    return selected

async def evaluate_redraft_quality(redraft: str, findings: List[Finding]) -> float:
    """
    Score redraft on:
    1. All high-confidence findings addressed (0.4)
    2. No new compliance issues introduced (0.3)
    3. Maintains original structure (0.2)
    4. Professional quality (0.1)
    """
    # Use a lightweight LLM to score quality
    score_prompt = f"""
Grade this redrafted document on a scale of 0-1 for:
1. Addresses all findings: {[f.description for f in findings]}
2. No new issues introduced
3. Structure preserved
4. Professional quality

Return only a JSON: {{"score": 0.0-1.0, "reasoning": "..."}}
"""

    result = await call_vertex_model("gemini-2.0-flash-001", score_prompt)
    return result['score']
```

**Report Synthesis Prompt**:

```python
REPORT_SYNTHESIS_PROMPT = """
You are creating the final Compliance Analysis Report.

# High-Confidence Findings (Score >= 0.90)
{findings_json}

# Document Context & Redrafted Content
{redrafted_content}

# Task: Generate a Two-Part Report
Follow this EXACT structure:

## PART 1: SUMMARY OF ANALYSIS
1. Group findings by their main Standard Heading (e.g., "SECTION 1.A. LEADERSHIP").
2. For each heading:
   - Provide a brief 'Description' of the section purpose.
   - List 'Key Areas Addressed' as bullet points.
   - List grouped 'Recommendations': Group related sections (e.g., "1.a.1.a, 1.a.1.b") and provide a cohesive "Summary of Issues" for that group.

## PART 2: DETAILED ANALYSIS BREAKDOWN
For EVERY section of the standard manual that the document failed to fulfill:
1. Output the section number (e.g., "1.a.1.a").
2. Output the "[BLACK TEXT] Actual Section from Standard Manual": {actual_manual_text}.
3. Output a list of "[RED TEXT] Identified Gaps": {list_of_issues}.
4. Output "[BLUE TEXT] Theraptly's Suggestions": {suggested_remediations}.

CRITICAL:
- Part 1 must be concise and high-level.
- Part 2 must be exhaustive and mirror the standard manual text exactly for the black text parts.
"""
```

---

### 7. Multi-LLM Final Verification

**Second Consensus Pass** (Criterion 12):

```python
async def final_multi_llm_verification(synthesized_document: str, original_findings: List[Finding]) -> VerificationResult:
    """
    Run synthesized document through ALL 3 LLMs again to verify:
    1. No hallucinations introduced
    2. All high-confidence findings addressed
    3. No new compliance issues created
    4. Internal consistency maintained
    """

    verification_prompt = """
You are verifying a compliance-enhanced document.

# Original High-Confidence Findings (that should be addressed)
{findings_summary}

# Synthesized Document
{synthesized_document}

# Verification Task
Check if this document:
1. Addresses ALL the findings above
2. Introduces NO new compliance issues
3. Contains NO hallucinated information
4. Maintains internal consistency

# Output (STRICT JSON)
{{
  "all_findings_addressed": true|false,
  "new_issues_found": [],
  "hallucinations_detected": [],
  "consistency_score": 0.0-1.0,
  "overall_pass": true|false,
  "reasoning": "detailed explanation"
}}
"""

    # Run all 3 models
    verifications = await asyncio.gather(
        call_vertex_model("gemini-2.5-pro", verification_prompt),
        call_vertex_model("claude-opus-4.5", verification_prompt),
        call_vertex_model("llama-4", verification_prompt)
    )

    # Aggregate verification scores
    avg_consistency = np.mean([v['consistency_score'] for v in verifications])
    all_pass = all([v['overall_pass'] for v in verifications])

    # Collect any issues flagged by any model
    all_new_issues = []
    for v in verifications:
        all_new_issues.extend(v.get('new_issues_found', []))

    final_confidence = avg_consistency if all_pass else avg_consistency * 0.7

    return VerificationResult(
        pass_verification=all_pass and final_confidence >= 0.85,
        confidence_score=final_confidence,
        new_issues=list(set(all_new_issues)),
        model_agreement=len([v for v in verifications if v['overall_pass']]) / 3
    )
```

---

### 8. Section-Specific Analysis

**Support for partial manual analysis** (user requirement):

```python
def retrieve_relevant_regulations(
    policy_text: str,
    compliance_body_id: int,
    compliance_section: Optional[str] = None  # e.g., "§3409-3412"
) -> List[RegulationText]:
    """
    Retrieve regulations based on scope:
    - If compliance_section specified: Filter to only that section
    - Otherwise: Search entire compliance body manual
    """

    # Generate embedding for policy text
    policy_embedding = vertex_embedding_service.generate_embedding(
        policy_text,
        task_type="RETRIEVAL_QUERY"
    )

    # Base query
    query = RegulationText.objects.filter(
        regulation__compliance_body_id=compliance_body_id
    )

    # Apply section filter if specified
    if compliance_section:
        # Parse section range (e.g., "§3409-3412" → ["§3409", "§3410", "§3411", "§3412"])
        section_pattern = parse_section_range(compliance_section)
        query = query.filter(
            Q(text__iregex=section_pattern)
        )

    # Vector similarity search
    results = query.annotate(
        similarity=CosineDistance('embedding_v2', policy_embedding)
    ).filter(
        similarity__gte=0.25
    ).order_by('-similarity')[:5]

    return results

def parse_section_range(section_str: str) -> str:
    """
    Parse section notation:
    - "§3409" → single section
    - "§3409-3412" → range of sections
    - Returns regex pattern for filtering
    """
    if '-' in section_str:
        start, end = section_str.replace('§', '').split('-')
        sections = [f"§{i}" for i in range(int(start), int(end) + 1)]
        return '|'.join(sections)
    else:
        return section_str
```

---

## Multi-Standard Support (CARF, MHRS, DBH)

### Regulatory Manual Format Differences

| Aspect               | CARF                        | MHRS                  | DBH               |
| -------------------- | --------------------------- | --------------------- | ----------------- |
| **Section Format**   | `1.B.`, `5.a.(2)(a)B.`      | `§3405.1`, `§3413.16` | Similar to MHRS   |
| **Hierarchy Depth**  | Up to 6 levels              | 2-3 levels            | 2-3 levels        |
| **Style**            | Narrative/Standards         | Legal/Regulatory      | Legal/Regulatory  |
| **Special Sections** | Intent Statements, Examples | Statutory Authority   | Rules/Definitions |

### Unified Section Parser

**Multi-Pattern Regex Engine**:

```python
import re
from typing import List, Tuple, Optional

class ComplianceBodySectionParser:
    """
    Flexible section parser supporting CARF, MH RS, and DBH formats
    """

    PATTERNS = {
        'carf': {
            # Matches: 1.B., 5.a.B., 5.a.(1)B., 5.a.(2)(a)B.
            'regex': r'(\d+\.[A-Z]\.(?:\([a-z]\))?(?:\(\d+\))?(?:\([a-z]\))?[A-Z]\.\s+\w+)',
            'description': 'Hierarchical alphanumeric with domain suffix'
        },
        'mhrs': {
            # Matches: §3405.1, §3413.16, §2-559
            'regex': r'(§\d+[-\.]?\d*\.?\d*)',
            'description': 'Section symbol with dot notation'
        },
        'dbh': {
            # Similar to MHRS
            'regex': r'(§\d+[-\.]?\d*\.?\d*|Rule\s+\d+\.?\d*)',
            'description': 'Section symbol or Rule notation'
        }
    }

    def __init__(self, compliance_body: str):
        self.body = compliance_body.lower()
        self.pattern = self.PATTERNS.get(self.body, self.PATTERNS['mhrs'])

    def extract_sections(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract all section references with positions
        Returns: [(section_ref, start_pos, end_pos), ...]
        """
        matches = []
        for match in re.finditer(self.pattern['regex'], text, re.MULTILINE):
            matches.append((
                match.group(1),
                match.start(),
                match.end()
            ))
        return matches

    def chunk_by_section(self, text: str, max_chunk_words: int = 1000) -> List[dict]:
        """
        Chunk document by sections, preserving context
        """
        sections = self.extract_sections(text)
        chunks = []

        for i, (section_ref, start, end) in enumerate(sections):
            # Get text until next section or end
            next_start = sections[i+1][1] if i+1 < len(sections) else len(text)
            section_text = text[start:next_start]

            # Handle long sections (split further if needed)
            words = section_text.split()
            if len(words) > max_chunk_words:
                # Sub-chunk while preserving section context
                for j in range(0, len(words), max_chunk_words):
                    chunk_words = words[j:j+max_chunk_words]
                    chunks.append({
                        'section_ref': section_ref,
                        'sub_chunk': j // max_chunk_words + 1 if len(words) > max_chunk_words else None,
                        'text': ' '.join(chunk_words),
                        'compliance_body': self.body
                    })
            else:
                chunks.append({
                    'section_ref': section_ref,
                    'sub_chunk': None,
                    'text': section_text,
                    'compliance_body': self.body
                })

        return chunks

    def parse_section_range(self, section_str: str) -> List[str]:
        """
        Parse section range notation for filtering
        Examples:
        - CARF: "1.B-1.E" → ["1.B.", "1.C.", "1.D.", "1.E."]
        - MHRS: "§3409-3412" → ["§3409", "§3410", "§3411", "§3412"]
        """
        if self.body == 'carf':
            # CARF uses letter ranges
            if '-' in section_str:
                # Parse "1.B-1.E"
                start_section, end_section = section_str.split('-')
                # Extract number and letters
                start_num = start_section.split('.')[0]
                start_letter = start_section.split('.')[1]
                end_letter = end_section.split('.')[1]

                # Generate range
                letters = [chr(i) for i in range(ord(start_letter), ord(end_letter) + 1)]
                return [f"{start_num}.{letter}." for letter in letters]
            else:
                return [section_str]

        else:  # MHRS/DBH
            # Numeric ranges
            if '-' in section_str:
                start, end = section_str.replace('§', '').split('-')
                sections = [f"§{i}" for i in range(int(start), int(end) + 1)]
                return sections
            else:
                return [section_str]
```

### Body-Specific Prompt Adjustments

```python
BODY_SPECIFIC_CONTEXT = {
    'carf': """
CARF Standards Context:
- This is a CARF Behavioral Health Standards Manual
- Section references use format: 1.B., 5.a.(2)(a)B.
- Standards include Intent Statements (purpose) and Examples (implementation)
- Focus on: governance, person-centered care, performance improvement
""",
    'mhrs': """
MHRS Regulations Context:
- This is an MHRS (DC Mental Health) regulatory manual
- Section references use format: §3405.1, §3413.16
- Regulations are legal requirements with statutory authority
- Focus on: consumer protections, service standards, certification
""",
    'dbh': """
DBH Rules Context:
- This is a DBH (Department of Behavioral Health) rules manual
- Section references use format: Rule 5.1, §2-559
- Rules govern licensing and operational requirements
- Focus on: licensing, safety, quality assurance
"""
}

def get_analysis_prompt(compliance_body: str, element_type: str) -> str:
    """Generate body-specific analysis prompt"""
    base_prompt = AGENT_PROMPTS[element_type]
    context = BODY_SPECIFIC_CONTEXT.get(compliance_body.lower(), "")

    return f"{context}\n\n{base_prompt}"
```

---

## Implementation Phases

### **Phase 1: Infrastructure & Extraction**

- [ ] **1.1** Set up FastAPI application with uvicorn
- [ ] **1.2** Configure SQLAlchemy 2.0 async engine with PostgreSQL + pgvector
- [ ] **1.3** Set up Alembic for database migrations
- [ ] **1.4** Create SQLAlchemy models (`DocumentElement`, `RegulationText`, `UploadedDocument`)
- [ ] **1.5** Run initial Alembic migration to create tables
- [ ] **1.6** Set up Google Document AI processors (Layout + Form Parser)
- [ ] **1.7** Implement `DocumentAIExtractor` service with full output parsing
- [ ] **1.8** Implement coordinate preservation (bounding boxes, vertices)
- [ ] **1.9** Build element type classifier (table/form/list/numbering/text)
- [ ] **1.10** Implement regulation manual ingestion workflow
- [ ] **1.11** Build section-specific retrieval logic with vector similarity
- [ ] **1.12** Test extraction with sample documents (verify structure preservation)

### **Phase 2: LangGraph Orchestration**

- [ ] **2.1** Define `RAGAnalysisState` schema with all fields
- [ ] **2.2** Implement element router (maps element types to agents)
- [ ] **2.3** Create prompt templates for each element type
- [ ] **2.4** Define Pydantic schemas for LLM output validation
- [ ] **2.5** Integrate Vertex AI Model Garden clients (Gemini, Claude, Llama)
- [ ] **2.6** Implement parallel multi-LLM execution with retry logic
- [ ] **2.7** Set up PostgreSQL checkpointer for state persistence
- [ ] **2.8** Build base LangGraph workflow graph

### **Phase 3: Consensus & Scoring**

- [ ] **3.1** Implement claim extraction from LLM outputs
- [ ] **3.2** Build semantic clustering (DBSCAN) for claim matching
- [ ] **3.3** Implement multi-dimensional confidence scoring formula
- [ ] **3.4** Build `GroundingValidator` (coordinate-based verification)
- [ ] **3.5** Implement conflict resolution logic
- [ ] **3.6** Add filtering (≥0.90 auto-include, 0.70-0.90 flag, <0.70 exclude)
- [ ] **3.7** Test consensus engine with mock data

### **Phase 4: Synthesis & Multi-Pass Verification**

- [ ] **4.1** Implement dual-model redrafting (Gemini + Claude)
- [ ] **4.2** Build redraft quality evaluation system
- [ ] **4.3** Implement final document synthesis
- [ ] **4.4** Build multi-LLM verification pipeline (second consensus pass)
- [ ] **4.5** Implement human-in-the-loop review queue (final output only)
- [ ] **4.6** Add comprehensive error handling and rollback

### **Phase 5: Output Format Generation**

- [ ] **5.1** Implement color-coded DOCX generator (python-docx with RGB colors)
- [ ] **5.2** Implement HTML output with CSS styling
- [ ] **5.3** Implement PDF generation (via ReportLab or WeasyPrint)
- [ ] **5.4** Implement JSON diff format
- [ ] **5.5** Build report generator (DOCX/PDF/TXT formats)
- [ ] **5.6** Implement format conversion pipeline

### **Phase 6: REST API Layer**

- [ ] **6.1** Implement `POST /api/regulations/upload` endpoint
- [ ] **6.2** Implement `POST /api/documents/analyze` endpoint
- [ ] **6.3** Implement `GET /api/documents/{id}/status` endpoint
- [ ] **6.4** Implement `GET /api/documents/{id}/result` (JSON) endpoint
- [ ] **6.5** Implement `GET /api/documents/{id}/report` (PDF/DOCX/TXT) endpoint
- [ ] **6.6** Implement `GET /api/documents/{id}/redraft` (all formats) endpoint
- [ ] **6.7** Add API authentication and rate limiting
- [ ] **6.8** Write API documentation (OpenAPI/Swagger)

### **Phase 7: Optimization & Production**

- [ ] **7.1** Implement Redis caching for LLM responses
- [ ] **7.2** Add token usage tracking and cost monitoring
- [ ] **7.3** Integrate LangSmith for pipeline observability
- [ ] **7.4** Set up Prometheus metrics (latency, throughput, error rates)
- [ ] **7.5** Implement progressive verification (resource optimization)
- [ ] **7.6** Load testing and performance tuning

---

## Verification Plan

### Automated Tests

1. **Unit Tests**:
   - Consensus clustering algorithm
   - Confidence scoring formula
   - Element routing logic
   - Grounding verification

2. **Integration Tests**:
   - Full document processing pipeline
   - Structure preservation verification
   - Multi-LLM parallel execution
   - State persistence and recovery

3. **Benchmarks**:
   - Compare vs. legacy single-LLM system
   - Precision/recall metrics
   - Processing time per document type
   - Cost per document analysis

### Manual Verification

1. **Human Review** (final output only per user request):
   - Compliance expert reviews synthesized documents
   - Validates high-confidence findings accuracy
   - Checks for hallucinations
   - Approves or requests revisions

2. **Visual Inspection**:
   - Document structure preservation
   - Layout fidelity (tables, forms, lists)
   - Professional quality assessment

---

## Technology Stack Summary

| Component         | Technology                                                        |
| ----------------- | ----------------------------------------------------------------- |
| **Extraction**    | GCP Document AI (Layout + Form Parser)                            |
| **Orchestration** | LangGraph with PostgreSQL checkpoints                             |
| **LLMs**          | Gemini 2.5 Pro, Claude Opus 4.5, Llama 4 (Vertex AI Model Garden) |
| **Embeddings**    | Vertex AI text-embedding-005 (768-dim)                            |
| **Clustering**    | scikit-learn DBSCAN                                               |
| **Database**      | PostgreSQL + pgvector                                             |
| **ORM**           | SQLAlchemy 2.0 (async)                                            |
| **Caching**       | Redis                                                             |
| **Monitoring**    | LangSmith + Prometheus                                            |
| **API Framework** | FastAPI                                                           |
| **Task Queue**    | Celery                                                            |

---

## Quality Assurance

- **Confidence Threshold**: ≥0.90 for auto-inclusion (per user: "higher is better")
- **Multi-Pass Verification**: All LLMs verify final output
- **Dual Redrafting**: Both Gemini and Claude generate, best selected
- **Human Oversight**: Final output review before delivery
- **Full Auditability**: All claims traceable to source coordinates
