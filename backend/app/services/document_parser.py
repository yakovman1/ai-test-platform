from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentType(ValueError):
    pass


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        document = DocxDocument(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise UnsupportedDocumentType(f"Unsupported file type: {suffix}")
