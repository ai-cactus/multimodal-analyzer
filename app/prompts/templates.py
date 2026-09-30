"""
Prompt templates for multi-LLM analysis
"""

ANALYSIS_SYSTEM_PROMPT = """You are an expert compliance analyst specializing in {compliance_body} standards.
Your task is to analyze document elements against relevant regulations and identify compliance gaps.

Output your findings in strict JSON format with the following structure:
{{
  "findings": [
    {{
      "issue_type": "gap|inconsistency|non-compliance|structural",
      "severity": "critical|major|minor",
      "description": "Clear description of the issue",
      "evidence": "Specific text from the document that demonstrates the issue",
      "regulation_ref": "Specific regulation section violated (e.g., §3409.1 or 1.B.5.a)",
      "recommendation": "Specific action to address the issue"
    }}
  ]
}}

Be precise and only report genuine compliance issues. Include the exact regulation reference."""

TABLE_ANALYSIS_PROMPT = """Analyze this table for compliance with {compliance_body} standards.

# TABLE CONTENT
{element_content}

# RELEVANT REGULATIONS
{regulations}

# ANALYSIS FOCUS
- Check if the table structure meets documentation requirements
- Verify all required fields/columns are present
- Ensure data completeness and accuracy
- Confirm proper labeling and formatting

Provide findings in JSON format."""

FORM_VALIDATION_PROMPT = """Validate this form against {compliance_body} requirements.

# FORM CONTENT
{element_content}

# RELEVANT REGULATIONS
{regulations}

# VALIDATION CHECKLIST
- All required fields present
- Proper field labeling
- Signature/approval sections complete
- Date fields appropriately placed
- Compliance with form standards

Provide findings in JSON format."""

LIST_ANALYSIS_PROMPT = """Analyze this list structure for compliance.

# LIST CONTENT
{element_content}

# RELEVANT REGULATIONS
{regulations}

# CHECK FOR
- Completeness of required items
- Proper numbering/ordering
- Missing mandatory elements
- Structural compliance

Provide findings in JSON format."""

CONTENT_ANALYSIS_PROMPT = """Analyze this text content for compliance gaps.

# TEXT CONTENT
{element_content}

# RELEVANT REGULATIONS
{regulations}

# ANALYZE FOR
- Required policy statements
- Mandatory procedures
- Missing documentation
- Regulatory language requirements
- Scope and coverage gaps

Provide findings in JSON format."""

REDRAFT_PROMPT = """You are redrafting a compliance document to address identified gaps.

# ORIGINAL CONTENT
{original_content}

# IDENTIFIED GAPS (High Confidence)
{findings}

# TASK
Create an improved version that:
1. Preserves all existing compliant content
2. Addresses each identified gap
3. Maintains professional tone
4. Ensures regulatory compliance

# RELEVANT REGULATIONS
{regulations}

Provide the redrafted content maintaining the original structure."""

QUALITY_SCORE_PROMPT = """Evaluate the quality of this redrafted compliance document.

# REDRAFT
{redraft_content}

# ORIGINAL ISSUES TO ADDRESS
{findings}

# SCORING CRITERIA (0-100 each)
1. Completeness: All gaps addressed
2. Clarity: Clear, professional language
3. Accuracy: Factually correct, no hallucinations
4. Compliance: Meets regulatory requirements

Respond with JSON:
{{
  "completeness_score": 0-100,
  "clarity_score": 0-100,
  "accuracy_score": 0-100,
  "compliance_score": 0-100,
  "overall_score": 0-100,
  "reasoning": "Brief explanation"
}}"""

VERIFICATION_PROMPT = """Verify this compliance analysis output for accuracy.

# SYNTHESIZED DOCUMENT
{synthesized_document}

# ORIGINAL HIGH-CONFIDENCE FINDINGS
{findings_summary}

# VERIFICATION TASKS
1. Confirm all findings are addressed
2. Check for new compliance issues introduced
3. Detect any hallucinated information
4. Assess internal consistency

Respond with JSON:
{{
  "all_findings_addressed": true|false,
  "new_issues_found": ["list any new issues"],
  "hallucinations_detected": ["list any hallucinations"],
  "consistency_score": 0.0-1.0,
  "overall_pass": true|false,
  "reasoning": "Detailed explanation"
}}"""

REPORT_SYNTHESIS_PROMPT = """Generate a professional Compliance Analysis Report.

# IDENTIFIED COMPLIANCE FINDINGS
{findings_json}

# DOCUMENT CONTEXT
{document_context}

# GENERATE TWO-PART REPORT

## PART 1: EXECUTIVE SUMMARY
Group findings by regulation section. For each section:
- Brief description of section purpose
- Key areas addressed
- Summary of recommendations (grouped by related sections)

## PART 2: DETAILED ANALYSIS
For each failed section:
1. Section number (e.g., "§3409.1")
2. [BLACK TEXT] Actual requirement from manual: {{exact_regulation_text}}
3. [RED TEXT] Identified gaps: {{specific_issues_found}}
4. [BLUE TEXT] Theraptly's recommendations: {{concrete_remediation_steps}}

Format as markdown. Use headers and bullet points for clarity. """


def get_analysis_prompt(element_type: str, compliance_body: str, element_content: str, regulations: str) -> tuple[str, str]:
    """
    Get appropriate prompt for element type
    
    Returns:
        (system_prompt, user_prompt)
    """
    system = ANALYSIS_SYSTEM_PROMPT.format(compliance_body=compliance_body)
    
    prompts = {
        "table": TABLE_ANALYSIS_PROMPT,
        "form": FORM_VALIDATION_PROMPT,
        "list_item": LIST_ANALYSIS_PROMPT,
        "text": CONTENT_ANALYSIS_PROMPT,
    }
    
    template = prompts.get(element_type, CONTENT_ANALYSIS_PROMPT)
    user = template.format(
        element_content=element_content,
        regulations=regulations,
        compliance_body=compliance_body
    )
    
    return system, user
