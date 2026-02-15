"""Text chunking strategies for document ingestion."""

from __future__ import annotations

import re


def fixed_size_chunks(text: str, chunk_size: int = 500, overlap: int = 50, **kwargs) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap
        if start >= text_len:
            break
        if end >= text_len:
            break

    return chunks


def sentence_chunks(text: str, chunk_size: int = 500, overlap: int = 1, **kwargs) -> list[str]:
    """Split text into chunks by sentences, respecting max chunk size."""
    if not text:
        return []

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text.strip()] if text.strip() else []

    chunks = []
    current_chunk: list[str] = []
    current_size = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_size + sentence_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep overlap sentences
            overlap_count = min(overlap, len(current_chunk))
            current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
            current_size = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_size += sentence_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def paragraph_chunks(text: str, chunk_size: int = 1000, **kwargs) -> list[str]:
    """Split text into chunks by paragraphs."""
    if not text:
        return []

    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks = []
    current_chunk: list[str] = []
    current_size = 0

    for para in paragraphs:
        para_len = len(para)

        if current_size + para_len > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_size = 0

        current_chunk.append(para)
        current_size += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def _build_breadcrumb(headers: dict[int, str], current_level: int) -> str:
    """Build a breadcrumb from the active header hierarchy.

    Example output: ``## Installation > ### Prerequisites``
    """
    if not headers:
        return ""
    parts = []
    for level in sorted(headers.keys()):
        if level <= current_level:
            prefix = "#" * level
            parts.append(f"{prefix} {headers[level]}")
    return " > ".join(parts)


def markdown_chunks(text: str, chunk_size: int = 1000, overlap: int = 0, **kwargs) -> list[str]:
    """Split markdown-formatted text into chunks based on header boundaries.

    Splits on header markers (``#`` through ``######``).  Preserves header
    hierarchy as a breadcrumb prefix on each chunk.  Combines small sections
    and splits large ones using paragraph/sentence fallback.
    """
    if not text or not text.strip():
        return []

    # --- Step 1: Parse sections ---
    sections: list[tuple[str, str]] = []  # (breadcrumb, content)
    current_headers: dict[int, str] = {}
    current_content_lines: list[str] = []
    current_level = 0

    for line in text.split("\n"):
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            # Save the previous section
            content = "\n".join(current_content_lines).strip()
            if content or current_level > 0:
                breadcrumb = _build_breadcrumb(current_headers, current_level)
                sections.append((breadcrumb, content))

            # Update header hierarchy
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            current_headers[level] = title
            # Clear deeper levels
            for lvl in [k for k in current_headers if k > level]:
                del current_headers[lvl]
            current_level = level
            current_content_lines = []
        else:
            current_content_lines.append(line)

    # Flush the last section
    content = "\n".join(current_content_lines).strip()
    if content or current_level > 0:
        breadcrumb = _build_breadcrumb(current_headers, current_level)
        sections.append((breadcrumb, content))

    if not sections:
        stripped = text.strip()
        return [stripped] if stripped else []

    # --- Step 2: Build chunks, combining small sections and splitting large ones ---
    chunks: list[str] = []
    pending_text = ""

    for breadcrumb, content in sections:
        if not content and not breadcrumb:
            continue

        # Build full section text
        if breadcrumb and content:
            section_text = f"{breadcrumb}\n\n{content}"
        elif breadcrumb:
            section_text = breadcrumb
        else:
            section_text = content

        # Large section — split with paragraph/sentence fallback
        if len(section_text) > chunk_size:
            if pending_text:
                chunks.append(pending_text)
                pending_text = ""

            prefix_len = len(breadcrumb) + 2 if breadcrumb else 0  # +2 for \n\n
            inner_size = max(chunk_size - prefix_len, 100)

            sub_chunks = paragraph_chunks(content, chunk_size=inner_size)
            # If paragraph splitting didn't actually reduce size, try sentences
            if not sub_chunks or any(len(sc) > inner_size for sc in sub_chunks):
                sub_chunks = sentence_chunks(content, chunk_size=inner_size)
            if not sub_chunks:
                sub_chunks = [content]

            for sc in sub_chunks:
                if breadcrumb:
                    chunks.append(f"{breadcrumb}\n\n{sc}")
                else:
                    chunks.append(sc)
        else:
            # Try to combine with pending
            if pending_text:
                combined = f"{pending_text}\n\n{section_text}"
            else:
                combined = section_text

            if len(combined) <= chunk_size:
                pending_text = combined
            else:
                if pending_text:
                    chunks.append(pending_text)
                pending_text = section_text

    if pending_text:
        chunks.append(pending_text)

    return chunks


_CHUNKERS = {
    "fixed_size": fixed_size_chunks,
    "sentence": sentence_chunks,
    "paragraph": paragraph_chunks,
    "markdown": markdown_chunks,
}


def get_chunker(strategy: str):
    """Return the chunking function for the given strategy name."""
    return _CHUNKERS.get(strategy, fixed_size_chunks)
