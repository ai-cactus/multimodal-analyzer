"""
Output generators package
"""
from app.services.output.docx_generator import get_docx_generator
from app.services.output.pdf_generator import get_pdf_generator
from app.services.output.html_generator import get_html_generator

__all__ = [
    "get_docx_generator",
    "get_pdf_generator",
    "get_html_generator",
]
