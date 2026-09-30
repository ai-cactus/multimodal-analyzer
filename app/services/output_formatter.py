"""
Output Formatter Service - Generate color-coded and clean compliance outputs
"""
from typing import List, Dict, Any, Optional
from docx import Document as DocxDocument
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX
import os
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger(__name__)


class OutputFormatter:
    """
    Formats compliance analysis outputs with color-coding and structure
    """
    
    # Color scheme
    COLOR_BLACK = RGBColor(0, 0, 0)  # Compliant content
    COLOR_RED = RGBColor(220, 20, 60)  # Gaps/issues (Crimson)
    COLOR_BLUE = RGBColor(0, 102, 204)  # Recommendations (Blue)
    HIGHLIGHT_YELLOW = WD_COLOR_INDEX.YELLOW  # Areas needing attention
    
    def format_color_coded_docx(
        self,
        original_text: str,
        high_confidence_findings: List[Dict[str, Any]],
        medium_confidence_findings: List[Dict[str, Any]],
        redraft_content: str,
        output_path: str
    ) -> str:
        """
        Generate color-coded DOCX with:
        - Black: Original compliant content
        - Red: Identified gaps
        - Blue: Recommendations
        
        Args:
            original_text: Original document text
            high_confidence_findings: High confidence compliance gaps
            medium_confidence_findings: Medium confidence gaps
            redraft_content: Redrafted compliant content
            output_path: Path to save output file
            
        Returns:
            Path to generated file
        """
        doc = DocxDocument()
        
        # Add header
        doc.add_heading('Compliance Analysis Report (Color-Coded)', 0)
        doc.add_paragraph(f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
        doc.add_page_break()
        
        # Add legend
        doc.add_heading('Color Legend', level=1)
        doc.add_paragraph('This document uses color-coding to highlight compliance status:')
        
        legend = doc.add_paragraph()
        run = legend.add_run('● Black Text: ')
        run.font.color.rgb = self.COLOR_BLACK
        legend.add_run('Compliant content meeting all requirements')
        
        legend = doc.add_paragraph()
        run = legend.add_run('● Red Text: ')
        run.font.color.rgb = self.COLOR_RED
        legend.add_run('Identified compliance gaps and issues')
        
        legend = doc.add_paragraph()
        run = legend.add_run('● Blue Text: ')
        run.font.color.rgb = self.COLOR_BLUE
        legend.add_run('Recommendations and corrective actions')
        
        doc.add_page_break()
        
        # Section 1: Findings Summary
        doc.add_heading('Section 1: Compliance Findings', level=1)
        
        doc.add_heading('High Confidence Findings', level=2)
        if high_confidence_findings:
            for idx, finding in enumerate(high_confidence_findings, 1):
                self._add_finding_to_doc(doc, idx, finding, is_high_confidence=True)
        else:
            p = doc.add_paragraph()
            run = p.add_run('✓ No high-confidence compliance gaps found.')
            run.font.color.rgb = RGBColor(0, 128, 0)  # Green
        
        doc.add_heading('Medium Confidence Findings', level=2)
        if medium_confidence_findings:
            for idx, finding in enumerate(medium_confidence_findings, 1):
                self._add_finding_to_doc(doc, idx, finding, is_high_confidence=False)
        else:
            doc.add_paragraph('No medium-confidence findings.')
        
        doc.add_page_break()
        
        # Section 2: Redrafted Document
        doc.add_heading('Section 2: Compliant Redraft (Color-Coded)', level=1)
        
        # Add redraft with inline highlighting
        self._add_redraft_with_highlights(
            doc, redraft_content, high_confidence_findings, medium_confidence_findings
        )
        
        doc.add_page_break()
        
        # Section 3: Recommendations
        doc.add_heading('Section 3: Recommended Actions', level=1)
        self._add_recommendations(doc, high_confidence_findings, medium_confidence_findings)
        
        # Save document
        doc.save(output_path)
        logger.info(f"Generated color-coded DOCX: {output_path}")
        
        return output_path
    
    def format_clean_docx(
        self,
        redraft_content: str,
        output_path: str,
        include_header: bool = False
    ) -> str:
        """
        Generate clean DOCX without any markup
        
        Args:
            redraft_content: Clean redrafted content
            output_path: Path to save output file
            include_header: Include generation header
            
        Returns:
            Path to generated file
        """
        doc = DocxDocument()
        
        if include_header:
            doc.add_heading('Compliant Document', 0)
            doc.add_paragraph(f'Finalized: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
            doc.add_page_break()
        
        # Add clean redraft paragraphs
        paragraphs = redraft_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                doc.add_paragraph(para.strip())
        
        doc.save(output_path)
        logger.info(f"Generated clean DOCX: {output_path}")
        
        return output_path
    
    def format_compliance_report_html(
        self,
        high_confidence: List[Dict],
        medium_confidence: List[Dict],
        document_context: str,
        iteration_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate HTML compliance report with executive summary
        
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .high-confidence {{ background: #ffe6e6; border-left: 4px solid #dc143c; padding: 15px; margin: 10px 0; }}
        .medium-confidence {{ background: #fff4e6; border-left: 4px solid #ff8c00; padding: 15px; margin: 10px 0; }}
        .finding-id {{ font-weight: bold; color: #555; }}
        .regulation-ref {{ font-style: italic; color: #0066cc; }}
        .critique-trail {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
        .executive-summary {{ background: #e8f4f8; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .iteration-history {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
    </style>
</head>
<body>
    <h1>Compliance Analysis Report</h1>
    <p><strong>Generated:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
    <p><strong>Document:</strong> {document_context}</p>
    
    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p><strong>High-Confidence Findings:</strong> {len(high_confidence)}</p>
        <p><strong>Medium-Confidence Findings:</strong> {len(medium_confidence)}</p>
        <p><strong>Total Issues:</strong> {len(high_confidence) + len(medium_confidence)}</p>
        
        {self._generate_iteration_summary_html(iteration_history) if iteration_history else ''}
    </div>
    
    <h2>High-Confidence Findings</h2>
    {self._generate_findings_html(high_confidence, is_high=True)}
    
    <h2>Medium-Confidence Findings</h2>
    {self._generate_findings_html(medium_confidence, is_high=False)}
    
</body>
</html>
"""
        return html
    
    def _add_finding_to_doc(
        self,
        doc: DocxDocument,
        idx: int,
        finding: Dict[str, Any],
        is_high_confidence: bool
    ):
        """Add a finding to the document with formatting"""
        # Finding header
        p = doc.add_paragraph()
        run = p.add_run(f"Finding #{idx}")
        run.bold = True
        run.font.size = Pt(12)
        
        # Error ID
        if finding.get('finding_id'):
            p2 = doc.add_paragraph(f"Error ID: {finding['finding_id']}")
            p2.style = 'List Bullet'
        
        # Description (RED)
        p = doc.add_paragraph()
        p.add_run('Issue: ').bold = True
        run = p.add_run(finding.get('description', 'N/A'))
        run.font.color.rgb = self.COLOR_RED
        
        # Regulation reference
        if finding.get('regulation_ref'):
            p = doc.add_paragraph()
            p.add_run('Regulation: ').bold = True
            run = p.add_run(finding['regulation_ref'])
            run.font.color.rgb = RGBColor(0, 0, 128)  # Navy
        
        # Confidence score
        confidence = finding.get('confidence', finding.get('confidence_score', 0))
        p = doc.add_paragraph(f"Confidence: {confidence:.2%}")
        
        # Critique trail (if available)
        if finding.get('critique_trail'):
            trail = finding['critique_trail']
            if isinstance(trail, list) and trail:
                p = doc.add_paragraph()
                p.add_run('Critique Trail: ').bold = True
                for step in trail:
                    if isinstance(step, dict):
                        p = doc.add_paragraph(f"  • {step.get('reasoning', 'N/A')}", style='List Bullet 2')
        
        doc.add_paragraph()  # Spacing
    
    def _add_redraft_with_highlights(
        self,
        doc: DocxDocument,
        redraft: str,
        high_conf: List[Dict],
        medium_conf: List[Dict]
    ):
        """Add redraft with inline color highlights"""
        # For now, add redraft as black text
        # In future, could parse and highlight specific corrected sections
        paragraphs = redraft.split('\n\n')
        for para in paragraphs:
            if para.strip():
                doc.add_paragraph(para.strip())
    
    def _add_recommendations(
        self,
        doc: DocxDocument,
        high_conf: List[Dict],
        medium_conf: List[Dict]
    ):
        """Add action recommendations"""
        all_findings = high_conf + medium_conf
        
        if not all_findings:
            doc.add_paragraph('No recommendations - document is fully compliant!')
            return
        
        # Group by regulation
        by_regulation = {}
        for finding in all_findings:
            reg_ref = finding.get('regulation_ref', 'General')
            if reg_ref not in by_regulation:
                by_regulation[reg_ref] = []
            by_regulation[reg_ref].append(finding)
        
        for reg_ref, findings in by_regulation.items():
            doc.add_heading(reg_ref, level=2)
            for finding in findings:
                p = doc.add_paragraph(style='List Bullet')
                run = p.add_run(finding.get('description', 'N/A'))
                run.font.color.rgb = self.COLOR_BLUE
    
    def _generate_findings_html(self, findings: List[Dict], is_high: bool) -> str:
        """Generate HTML for findings list"""
        if not findings:
            return '<p>No findings.</p>'
        
        css_class = 'high-confidence' if is_high else 'medium-confidence'
        html = ''
        
        for idx, finding in enumerate(findings, 1):
            finding_id = finding.get('finding_id', f'finding-{idx}')
            description = finding.get('description', 'N/A')
            reg_ref = finding.get('regulation_ref', '')
            confidence = finding.get('confidence', finding.get('confidence_score', 0))
            
            html += f"""
            <div class="{css_class}">
                <p class="finding-id">Finding #{idx} (ID: {finding_id})</p>
                <p><strong>Issue:</strong> {description}</p>
                {f'<p class="regulation-ref">Regulation: {reg_ref}</p>' if reg_ref else ''}
                <p><strong>Confidence:</strong> {confidence:.1%}</p>
            </div>
            """
        
        return html
    
    def _generate_iteration_summary_html(self, iteration_history: List[Dict]) -> str:
        """Generate iteration summary table"""
        if not iteration_history:
            return ''
        
        html = '<div class="iteration-history"><h3>Iteration History</h3><table>'
        html += '<tr><th>Iteration</th><th>High Conf.</th><th>Med Conf.</th><th>Status</th></tr>'
        
        for entry in iteration_history:
            iteration = entry.get('iteration', 0)
            high = entry.get('high_confidence_findings', 0)
            medium = entry.get('medium_confidence_findings', 0)
            converged = entry.get('converged', False)
            status = '✓ Converged' if converged else 'In Progress'
            
            html += f'<tr><td>{iteration + 1}</td><td>{high}</td><td>{medium}</td><td>{status}</td></tr>'
        
        html += '</table></div>'
        return html


# Singleton
_output_formatter = None


def get_output_formatter() -> OutputFormatter:
    """Get or create singleton output formatter"""
    global _output_formatter
    if _output_formatter is None:
        _output_formatter = OutputFormatter()
    return _output_formatter
