"""Extracts plain text from a resume PDF using pdfplumber, capped to a page limit."""

from __future__ import annotations

import io
from typing import Optional, Union

import pdfplumber


def read_pdf_text(source: Union[str, bytes], max_pages: Optional[int] = None) -> str:
    """Extract text from a PDF given either a filesystem path or raw PDF bytes.

    Accepting bytes directly means callers never need to write the upload to
    disk first - important once the server has no guarantee of a persistent,
    shared filesystem between requests (e.g. running on Lambda).
    """
    try:
        text_parts = []
        target = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
        with pdfplumber.open(target) as pdf:
            pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for p in pages:
                text_parts.append(p.extract_text() or "")
        return "\n".join(text_parts).strip()
    except Exception as e:
        return f"PDF_READ_ERROR: {e}"

