"""PDF hashing, text extraction, and page-local chunking helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List

import pdfplumber


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file as uppercase hexadecimal."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def extract_pdf_pages(path: Path) -> List[Dict[str, object]]:
    """Extract text from each PDF page using 1-based page numbers."""
    pages: List[Dict[str, object]] = []
    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"pdf_page": index, "text": text})
    return pages


def _chunk_id(
    *,
    source_document_sha256: str,
    pdf_page: int,
    char_start: int,
    char_end: int,
    text: str,
) -> str:
    payload = "|".join(
        [
            source_document_sha256.upper(),
            str(pdf_page),
            str(char_start),
            str(char_end),
            text,
        ]
    )
    return "chunk_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def chunk_text_by_page(
    pages: List[Dict[str, object]],
    *,
    source_document_relative_path: str,
    source_document_sha256: str,
    chunk_size: int = 1600,
    chunk_overlap: int = 200,
) -> List[Dict[str, object]]:
    """Split page text into stable chunks without crossing page boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: List[Dict[str, object]] = []
    step = chunk_size - chunk_overlap
    for page in pages:
        pdf_page = int(page["pdf_page"])
        text = str(page.get("text") or "")
        if not text.strip():
            continue
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "chunk_id": _chunk_id(
                            source_document_sha256=source_document_sha256,
                            pdf_page=pdf_page,
                            char_start=start,
                            char_end=end,
                            text=chunk_text,
                        ),
                        "source_document_relative_path": source_document_relative_path,
                        "source_document_sha256": source_document_sha256.upper(),
                        "pdf_page": pdf_page,
                        "char_start": start,
                        "char_end": end,
                        "text": chunk_text,
                    }
                )
            if end >= len(text):
                break
            start += step
    return chunks
