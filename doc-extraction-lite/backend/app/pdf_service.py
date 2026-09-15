import fitz  # PyMuPDF
import os
from typing import Dict

MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", 25))
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

class PDFServiceError(Exception):
    pass

def validate_pdf(file_content: bytes):
    if len(file_content) > MAX_PDF_SIZE_BYTES:
        raise PDFServiceError(f"PDF file size exceeds {MAX_PDF_SIZE_MB}MB limit.")
    try:
        fitz.open(stream=file_content, filetype="pdf")
    except Exception as e:
        raise PDFServiceError(f"Invalid PDF file: {e}")

def extract_text_per_page(file_content: bytes) -> Dict[str, str]:
    doc = fitz.open(stream=file_content, filetype="pdf")
    page_texts = {}
    for i, page in enumerate(doc):
        page_texts[str(i + 1)] = page.get_text()
    doc.close()
    return page_texts
