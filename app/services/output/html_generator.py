"""
HTML Generator - Creates web-viewable compliance documents
"""
from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        .legend {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .legend span {{
            display: inline-block;
            margin-right: 20px;
            font-weight: bold;
        }}
        
        .unchanged {{ color: #000000; }}
        .modified {{ color: #0000FF; }}
        .added {{ color: #FF0000; }}
        
        .finding {{
            background: #fff;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .finding-header {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 10px;
        }}
        
        .severity-critical {{ border-left-color: #e74c3c; }}
        .severity-major {{ border-left-color: #f39c12; }}
        .severity-minor {{ border-left-color: #3498db; }}
        
        .meta {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 10px;
        }}
        
        .recommendation {{
            background: #e8f4f8;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Compliance Analysis Report</h1>
        
        <div class="legend">
            <span class="unchanged">⬤ Compliant Content</span>
            <span class="modified">⬤ Recommended Modifications</span>
            <span class="added">⬤ New Requirements</span>
        </div>
        
        <h2>Executive Summary</h2>
        <p>{summary}</p>
        
        <h2>Identified Compliance Gaps</h2>
        {findings_html}
        
        <h2>Recommendations</h2>
        <div class="modified">
            {recommendations_html}
        </div>
    </div>
</body>
</html>
"""


class HTMLGenerator:
    """
    Generates HTML compliance documents with interactive features
    """
    
    def generate_html_report(
        self,
        findings: List[Dict],
        document_context: Dict,
        output_path: str
    ) -> str:
        """
        Generate interactive HTML report
        
        Args:
            findings: High-confidence findings
            document_context: Document metadata
            output_path: Where to save HTML
            
        Returns:
            Path to generated HTML
        """
        logger.info(f"Generating HTML report: {output_path}")
        
        # Generate summary
        summary = f"Analysis of {document_context.get('filename', 'document')} identified {len(findings)} compliance gaps."
        
        # Generate findings HTML
        findings_html = ""
        for i, finding in enumerate(findings):
            severity = finding.get('severity', 'minor').lower()
            findings_html += f"""
            <div class="finding severity-{severity}">
                <div class="finding-header">
                    Finding #{i+1}: {finding.get('issue_type', 'Compliance Gap')}
                </div>
                <p><strong>Description:</strong> <span class="added">{finding.get('description', 'N/A')}</span></p>
                <p><strong>Evidence:</strong> {finding.get('evidence', 'N/A')}</p>
                <div class="recommendation">
                    <strong>Recommendation:</strong> {finding.get('recommendation', 'Address this compliance gap.')}
                </div>
                <div class="meta">
                    Regulation: {finding.get('regulation_ref', 'N/A')} | 
                    Severity: {finding.get('severity', 'N/A').upper()}
                </div>
            </div>
            """
        
        # Generate recommendations HTML
        recommendations_html = "<ul>"
        for finding in findings:  # No limit
            recommendations_html += f"<li>{finding.get('recommendation', 'Address this gap')}</li>"
        recommendations_html += "</ul>"
        
        # Build final HTML
        html_content = HTML_TEMPLATE.format(
            summary=summary,
            findings_html=findings_html,
            recommendations_html=recommendations_html
        )
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML saved to {output_path}")
        return output_path


def get_html_generator() -> HTMLGenerator:
    """Get HTMLGenerator instance"""
    return HTMLGenerator()
