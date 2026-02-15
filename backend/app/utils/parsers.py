"""Document parsers for various file formats."""

from __future__ import annotations

import csv
import io
import json

from app.utils.logger import logger


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        logger.error("Failed to parse PDF {}: {}", file_path, e)
        raise


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error("Failed to parse DOCX {}: {}", file_path, e)
        raise


def parse_txt(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_csv(file_path: str) -> str:
    """Read a CSV file and convert rows to text."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = []
        headers = None
        for i, row in enumerate(reader):
            if i == 0:
                headers = row
                continue
            if headers:
                row_text = ", ".join(f"{h}: {v}" for h, v in zip(headers, row) if v.strip())
            else:
                row_text = ", ".join(row)
            if row_text.strip():
                rows.append(row_text)
        return "\n".join(rows)


def parse_json(file_path: str) -> str:
    """Read a JSON file and flatten to text."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def flatten(obj, prefix=""):
        lines = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                lines.extend(flatten(v, f"{prefix}{k}: "))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                lines.extend(flatten(item, f"{prefix}[{i}] "))
        else:
            lines.append(f"{prefix}{obj}")
        return lines

    return "\n".join(flatten(data))


def parse_markdown(file_path: str) -> str:
    """Read a markdown file and return as plain text."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Simple markdown stripping
    import re
    text = re.sub(r'#{1,6}\s+', '', text)  # Remove headers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
    text = re.sub(r'`(.+?)`', r'\1', text)  # Inline code
    text = re.sub(r'```[\s\S]*?```', '', text)  # Code blocks
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
    text = re.sub(r'!\[.*?\]\(.+?\)', '', text)  # Images

    return text


_PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "txt": parse_txt,
    "csv": parse_csv,
    "json": parse_json,
    "md": parse_markdown,
    "markdown": parse_markdown,
}


def parse_document(file_path: str, file_type: str) -> str:
    """Parse a document based on its file type."""
    file_type = file_type.lower().lstrip(".")
    parser = _PARSERS.get(file_type)
    if parser is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser(file_path)
