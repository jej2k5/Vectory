"""Document parsers for various file formats."""

from __future__ import annotations

import csv
import io
import json
import re

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


def _extract_frontmatter(text: str) -> tuple[str, dict]:
    """Extract YAML frontmatter from markdown text.

    Returns (markdown_without_frontmatter, frontmatter_dict).
    Parses simple ``key: value`` lines; nested YAML is not supported.
    """
    if not text.startswith("---"):
        return text, {}

    # Find the closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return text, {}

    frontmatter_block = text[3:end].strip()
    body = text[end + 4:]  # skip past \n---

    metadata: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        match = re.match(r"^(\w[\w\s]*?):\s*(.+)$", line.strip())
        if match:
            metadata[match.group(1).strip()] = match.group(2).strip()

    return body, metadata


def parse_markdown(file_path: str) -> str:
    """Read a markdown file and convert to structured plain text.

    Uses the ``markdown`` library to convert to HTML, then ``BeautifulSoup``
    to extract clean text.  Header ``#`` markers are preserved so that the
    markdown-aware chunker can split on them.  Code-block content is indented
    by four spaces to prevent false header matches.
    """
    import markdown as md_lib
    from bs4 import BeautifulSoup, NavigableString

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    body, _meta = _extract_frontmatter(raw)

    html = md_lib.markdown(body, extensions=["tables", "fenced_code"])
    soup = BeautifulSoup(html, "html.parser")

    parts: list[str] = []

    for element in soup.children:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                parts.append(text)
            continue

        tag = element.name

        # Headings — preserve # markers
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            prefix = "#" * level
            parts.append(f"{prefix} {element.get_text().strip()}")

        # Code blocks — indent to avoid false header matches
        elif tag == "pre":
            code = element.find("code")
            code_text = code.get_text() if code else element.get_text()
            indented = "\n".join(f"    {line}" for line in code_text.splitlines())
            parts.append(indented)

        # Tables
        elif tag == "table":
            rows: list[str] = []
            for tr in element.find_all("tr"):
                cells = [
                    td.get_text().strip()
                    for td in tr.find_all(["th", "td"])
                ]
                rows.append(" | ".join(cells))
            parts.append("\n".join(rows))

        # Lists
        elif tag in ("ul", "ol"):
            for i, li in enumerate(element.find_all("li", recursive=False), 1):
                bullet = f"{i}." if tag == "ol" else "-"
                parts.append(f"{bullet} {li.get_text().strip()}")

        # Blockquotes
        elif tag == "blockquote":
            quote_lines = element.get_text().strip().splitlines()
            parts.append("\n".join(f"> {line}" for line in quote_lines))

        # Everything else (p, div, etc.)
        else:
            text = element.get_text().strip()
            if text:
                parts.append(text)

    result = "\n\n".join(parts)
    # Collapse excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip("\n")


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
