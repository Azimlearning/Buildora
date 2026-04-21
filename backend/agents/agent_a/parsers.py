"""
Agent A: PDF Parsers

Handles both digital and scanned PDF documents

Author: Chip/Azim
"""

import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from typing import Optional
import io


def extract_text_pdfplumber(pdf_path: str) -> Optional[str]:
    """
    Extract text from digital PDF using pdfplumber

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text or None if failed
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            # Check if we got meaningful text
            if len(text.strip()) > 100:
                return text.strip()

        return None
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
        return None


def extract_text_ocr(pdf_path: str) -> str:
    """
    Extract text from scanned PDF using PyMuPDF + Tesseract OCR

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text via OCR
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Run OCR
            page_text = pytesseract.image_to_string(img, lang="eng")
            text += page_text + "\n"

        doc.close()
        return text.strip()

    except Exception as e:
        print(f"OCR extraction failed: {e}")
        return ""


def parse_pdf(pdf_path: str) -> str:
    """
    Main PDF parsing function with fallback strategy

    Strategy:
    1. Try pdfplumber (fast, works for digital PDFs)
    2. Fall back to OCR (slower, works for scanned PDFs)

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    # Try digital extraction first
    text = extract_text_pdfplumber(pdf_path)

    if text:
        print(f"✓ Extracted text using pdfplumber ({len(text)} chars)")
        return text

    # Fall back to OCR
    print("⚠ pdfplumber failed, falling back to OCR...")
    text = extract_text_ocr(pdf_path)

    if text:
        print(f"✓ Extracted text using OCR ({len(text)} chars)")
        return text

    raise ValueError("Failed to extract text from PDF using both methods")


def extract_tables(pdf_path: str) -> list[dict]:
    """
    Extract tables from PDF using pdfplumber

    Args:
        pdf_path: Path to PDF file

    Returns:
        List of table dictionaries
    """
    tables = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table in page_tables:
                    tables.append({
                        "page": page_num + 1,
                        "data": table
                    })

    except Exception as e:
        print(f"Table extraction failed: {e}")

    return tables
