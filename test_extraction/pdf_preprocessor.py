"""
PDF Preprocessor - Extracts and cleans text from PDF files (research papers).
Produces cleaned plaintext suitable for downstream concept extraction.
"""

import os
import re
import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from all pages of a PDF using pdfplumber."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                logger.warning(f"Page {i + 1} of {pdf_path} yielded no text.")
    return "\n\n".join(pages_text)


def clean_extracted_text(raw_text: str) -> str:
    """Clean raw PDF-extracted text for downstream NLP use."""
    # Normalize unicode characters
    text = raw_text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Remove page numbers (standalone numbers on their own line)
    text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", text)

    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove hyphenation at line breaks (e.g., "trans-\nformer" -> "transformer")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Remove empty lines at start/end
    text = text.strip()

    return text


def process_pdf(pdf_path: str, output_path: str) -> str:
    """
    Full pipeline: extract text from PDF, clean it, and save to output file.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Path to write the cleaned text output.

    Returns:
        The cleaned text content.
    """
    logger.info(f"Processing PDF: {pdf_path}")

    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        logger.error(f"No text extracted from {pdf_path}")
        return ""

    cleaned_text = clean_extracted_text(raw_text)

    # Prepend source metadata header
    filename = Path(pdf_path).stem
    header = (
        f"SOURCE_TYPE: pdf\n"
        f"SOURCE_FILE: {Path(pdf_path).name}\n"
        f"CHAR_COUNT: {len(cleaned_text)}\n"
        f"---\n\n"
    )

    output_content = header + cleaned_text

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_content)

    logger.info(
        f"Saved cleaned text to {output_path} "
        f"({len(cleaned_text)} chars, ~{len(cleaned_text.split())} words)"
    )
    return cleaned_text
