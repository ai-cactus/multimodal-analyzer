"""
DOCX Generator - Creates color-coded compliance documents
"""
from docx import Document
from docx.shared import RGBColor, Pt
from typing import List, Dict
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)


class DOCXGenerator:
    """
    Generates color-coded DOCX documents following compliance standards
    
    Color scheme:
    - Black (0,0,0): Unchanged/compliant text
    - Blue (0,0,255): Modifications/improvements
    - Red (255,0,0): New additions/critical gaps
    """
    
    COLOR_MAPPING = {
        "unchanged": RGBColor(0, 0, 0),      # Black
        "modified": RGBColor(0, 0, 255),     # Blue
        "added": RGBColor(255, 0, 0),        # Red
    }
    
    def generate_color_coded_document(
        self,
        original_content: str,
        findings: List[Dict],
        redraft_content: str,
        output_path: str
    ) -> str:
        """
        Generate color-coded DOCX document
        
        Args:
            original_content: Original document text
            findings: List of high-confidence findings
            redraft_content: Redrafted content with improvements
            output_path: Where to save the DOCX
            
        Returns:
            Path to generated document
        """
        logger.info(f"Generating color-coded DOCX: {output_path}")
        
        doc = Document()
        
        # Add title
        title = doc.add_heading('Compliance Analysis - Color-Coded Document', 0)
        
        # Add legend
        legend = doc.add_paragraph()
        legend.add_run('Legend: ').bold = True
        
        black_run = legend.add_run('Black = Compliant  ')
        black_run.font.color.rgb = self.COLOR_MAPPING["unchanged"]
        
        blue_run = legend.add_run('Blue = Modified  ')
        blue_run.font.color.rgb = self.COLOR_MAPPING["modified"]
        
        red_run = legend.add_run('Red = New Addition')
        red_run.font.color.rgb = self.COLOR_MAPPING["added"]
        
        doc.add_paragraph()  # Spacing
        
        # Process content with color coding
        self._add_color_coded_content(doc, original_content, findings, redraft_content)
        
        # Save document
        doc.save(output_path)
        logger.info(f"DOCX saved to {output_path}")
        
        return output_path
    
    def _add_color_coded_content(
        self,
        doc: Document,
        original: str,
        findings: List[Dict],
        redraft: str
    ):
        """Add color-coded content to document"""
        
        # Section: Original Content (Black)
        doc.add_heading('Original Content', level=1)
        original_para = doc.add_paragraph()
        original_run = original_para.add_run(original)
        original_run.font.color.rgb = self.COLOR_MAPPING["unchanged"]
        
        # Section: Identified Gaps (Red)
        doc.add_heading('Identified Compliance Gaps', level=1)
        if not findings:
            doc.add_paragraph("No high-confidence compliance gaps identified.")
        else:
            for i, finding in enumerate(findings):
                para = doc.add_paragraph()
                para.add_run(f"{i+1}. ").bold = True
                
                issue_run = para.add_run(finding.get('description', 'N/A'))
                issue_run.font.color.rgb = self.COLOR_MAPPING["added"]
                
                # Add regulation reference
                reg_ref = finding.get('regulation_ref', 'N/A')
                para.add_run(f"\n   Reference: {reg_ref}").font.size = Pt(9)
        
        # Section: Recommended Changes (Blue)
        doc.add_heading('Recommended Improvements', level=1)
        redraft_para = doc.add_paragraph()
        redraft_run = redraft_para.add_run(redraft)
        redraft_run.font.color.rgb = self.COLOR_MAPPING["modified"]
    
    def generate_clean_document(
        self,
        redraft_content: str,
        output_path: str
    ) -> str:
        """Generate clean (no color coding) professional document with proper formatting"""
        
        logger.info(f"Generating clean DOCX: {output_path}")
        
        doc = Document()
        doc.add_heading('Compliance Document - Improved Version', 0)
        
        # Parse markdown-style content and convert to DOCX
        self._add_formatted_content(doc, redraft_content)
        
        doc.save(output_path)
        logger.info(f"Clean DOCX saved to {output_path}")
        
        return output_path
    
    def _add_formatted_content(self, doc: Document, content: str):
        """
        Parse markdown-style content and add properly formatted DOCX elements
        
        Handles:
        - ### Headings
        - **Bold** text
        - Numbered lists (1. 2. 3.)
        - Regular paragraphs
        """
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Handle markdown headings
            if line.startswith('###'):
                heading_text = line.replace('###', '').strip()
                doc.add_heading(heading_text, level=2)
                i += 1
                continue
            
            elif line.startswith('##'):
                heading_text = line.replace('##', '').strip()
                doc.add_heading(heading_text, level=1)
                i += 1
                continue
            
            elif line.startswith('#'):
                heading_text = line.replace('#', '').strip()
                doc.add_heading(heading_text, level=1)
                i += 1
                continue
            
            # Handle numbered lists (1. 2. 3.)
            if len(line) > 0 and line[0].isdigit() and '. ' in line[:5]:
                # Extract list items
                list_items = []
                while i < len(lines):
                    current_line = lines[i].strip()
                    if current_line and len(current_line) > 0 and current_line[0].isdigit() and '. ' in current_line[:5]:
                        # Remove number prefix for cleaner display
                        item_text = current_line.split('. ', 1)[1] if '. ' in current_line else current_line
                        list_items.append(item_text)
                        i += 1
                    elif current_line and not current_line.startswith((' ', '\t')):
                        # Not indented, end of list
                        break
                    elif current_line:
                        # Continuation of previous item (indented)
                        if list_items:
                            list_items[-1] += " " + current_line
                        i += 1
                    else:
                        i += 1
                        break
                
                # Add numbered list items
                for idx, item in enumerate(list_items, 1):
                    para = doc.add_paragraph(style='List Number')
                    self._add_formatted_text(para, item)
                continue
            
            # Handle regular paragraphs with inline formatting
            para = doc.add_paragraph()
            self._add_formatted_text(para, line)
            i += 1
    
    def _add_formatted_text(self, paragraph, text: str):
        """
        Add text to paragraph with inline formatting (bold, italic)
        Handles **bold** and *italic* markdown
        """
        # Split by bold markers
        parts = re.split(r'(\*\*.*?\*\*)', text)
        
        for part in parts:
            if not part:
                continue
                
            # Check if this part is bold
            if part.startswith('**') and part.endswith('**'):
                # Remove markers and add as bold
                bold_text = part[2:-2]
                run = paragraph.add_run(bold_text)
                run.bold = True
            else:
                # Regular text (could still have italic)
                italic_parts = re.split(r'(\*.*?\*)', part)
                for ipart in italic_parts:
                    if not ipart:
                        continue
                    if ipart.startswith('*') and ipart.endswith('*') and not ipart.startswith('**'):
                        italic_text = ipart[1:-1]
                        run = paragraph.add_run(italic_text)
                        run.italic = True
                    else:
                        paragraph.add_run(ipart)

    def generate_compliance_report(
        self,
        findings: List[Dict],
        document_context: Dict,
        output_path: str
    ) -> str:
        """
        Generate professional DOCX compliance report
        """
        logger.info(f"Generating DOCX report: {output_path}")
        
        doc = Document()
        
        # Title
        doc.add_heading('Compliance Analysis Report', 0)
        
        # Executive Summary
        doc.add_heading('Executive Summary', level=1)
        summary = doc.add_paragraph()
        summary.add_run(f"This report presents compliance analysis results for {document_context.get('filename', 'the uploaded document')}.")
        summary.add_run(f"\nAnalysis identified {len(findings)} high-confidence compliance gaps.")
        
        # Findings Table
        doc.add_heading('Findings Summary', level=2)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = '#'
        hdr_cells[1].text = 'Severity'
        hdr_cells[2].text = 'Issue Type'
        hdr_cells[3].text = 'Regulation'
        
        for i, finding in enumerate(findings[:20]):
            row_cells = table.add_row().cells
            row_cells[0].text = str(i+1)
            row_cells[1].text = finding.get('severity', 'N/A')
            row_cells[2].text = finding.get('issue_type', 'N/A')
            row_cells[3].text = finding.get('regulation_ref', 'N/A')[:30]
            
        # Detailed Findings
        doc.add_heading('Detailed Findings', level=1)
        for i, finding in enumerate(findings):
            doc.add_heading(f"Finding #{i+1}: {finding.get('description', 'N/A')}", level=3)
            
            p = doc.add_paragraph()
            p.add_run("Evidence: ").bold = True
            p.add_run(finding.get('evidence', 'N/A'))
            
            p = doc.add_paragraph()
            p.add_run("Regulation Reference: ").bold = True
            p.add_run(finding.get('regulation_ref', 'N/A'))
            
            p = doc.add_paragraph()
            p.add_run("Recommendation: ").bold = True
            p.add_run(finding.get('recommendation', 'Address this gap'))
            
            doc.add_paragraph() # Spacing
            
        doc.save(output_path)
        return output_path


def get_docx_generator() -> DOCXGenerator:
    """Get DOCXGenerator instance"""
    return DOCXGenerator()
