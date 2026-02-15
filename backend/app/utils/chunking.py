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


_CHUNKERS = {
    "fixed_size": fixed_size_chunks,
    "sentence": sentence_chunks,
    "paragraph": paragraph_chunks,
}


def get_chunker(strategy: str):
    """Return the chunking function for the given strategy name."""
    return _CHUNKERS.get(strategy, fixed_size_chunks)
