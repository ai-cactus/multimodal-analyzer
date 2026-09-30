"""
PDF Generator - Creates professional PDF reports
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue, red, HexColor
from reportlab.lib.units import inch
from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFGenerator:
    """
    Generates professional PDF compliance reports
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with colors"""
        
        # Unchanged text (Black)
        self.styles.add(ParagraphStyle(
            name='Unchanged',
            parent=self.styles['Normal'],
            textColor=black
        ))
        
        # Modified text (Blue)
        self.styles.add(ParagraphStyle(
            name='Modified',
            parent=self.styles['Normal'],
            textColor=blue
        ))
        
        # New additions (Red)
        self.styles.add(ParagraphStyle(
            name='Added',
            parent=self.styles['Normal'],
            textColor=red
        ))
    
    def generate_compliance_report(
        self,
        findings: List[Dict],
        document_context: Dict,
        output_path: str
    ) -> str:
        """
        Generate comprehensive PDF compliance report
        
        Args:
            findings: High-confidence findings
            document_context: Document metadata
            output_path: Where to save PDF
            
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating PDF report: {output_path}")
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        title_style = self.styles['Title']
        story.append(Paragraph("Compliance Analysis Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        summary_text = f"""
        This report presents the compliance analysis results for {document_context.get('filename', 'the uploaded document')}.
        Analysis identified {len(findings)} high-confidence compliance gaps that require attention.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Findings Summary Table
        story.append(Paragraph("Findings Summary", self.styles['Heading2']))
        
        table_data = [['#', 'Severity', 'Issue Type', 'Regulation']]
        for i, finding in enumerate(findings):  # No limit
            table_data.append([
                str(i+1),
                finding.get('severity', 'N/A'),
                finding.get('issue_type', 'N/A'),
                finding.get('regulation_ref', 'N/A')
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC'))
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed Findings
        story.append(PageBreak())
        story.append(Paragraph("Detailed Findings", self.styles['Heading1']))
        
        for i, finding in enumerate(findings):
            story.append(Paragraph(f"Finding #{i+1}: {finding.get('description', 'N/A')}", self.styles['Heading3']))
            
            # Evidence (Black)
            story.append(Paragraph("<b>Evidence:</b>", self.styles['Normal']))
            story.append(Paragraph(finding.get('evidence', 'N/A'), self.styles['Unchanged']))
            
            # Regulation (Red)
            story.append(Paragraph("<b>Regulation Reference:</b>", self.styles['Normal']))
            story.append(Paragraph(finding.get('regulation_ref', 'N/A'), self.styles['Added']))
            
            # Recommendation (Blue)
            story.append(Paragraph("<b>Recommendation:</b>", self.styles['Normal']))
            story.append(Paragraph(finding.get('recommendation', 'Address this gap'), self.styles['Modified']))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF saved to {output_path}")
        
        return output_path


def get_pdf_generator() -> PDFGenerator:
    """Get PDFGenerator instance"""
    return PDFGenerator()
