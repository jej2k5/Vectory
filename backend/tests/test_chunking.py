"""Tests for text chunking utilities."""
import pytest

from app.utils.chunking import (
    fixed_size_chunks,
    sentence_chunks,
    paragraph_chunks,
    markdown_chunks,
    get_chunker,
)


class TestFixedSizeChunks:
    def test_basic_chunking(self):
        text = "a" * 1000
        chunks = fixed_size_chunks(text, chunk_size=200, overlap=0)
        assert len(chunks) == 5
        assert all(len(c) == 200 for c in chunks)

    def test_overlap(self):
        text = "a" * 500
        chunks = fixed_size_chunks(text, chunk_size=200, overlap=50)
        assert len(chunks) >= 3

    def test_empty_text(self):
        assert fixed_size_chunks("") == []

    def test_short_text(self):
        chunks = fixed_size_chunks("hello", chunk_size=100, overlap=0)
        assert len(chunks) == 1
        assert chunks[0] == "hello"


class TestSentenceChunks:
    def test_basic_sentences(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = sentence_chunks(text, chunk_size=50, overlap=0)
        assert len(chunks) >= 2

    def test_empty_text(self):
        assert sentence_chunks("") == []

    def test_single_sentence(self):
        chunks = sentence_chunks("Just one sentence.", chunk_size=100)
        assert len(chunks) == 1


class TestParagraphChunks:
    def test_basic_paragraphs(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = paragraph_chunks(text, chunk_size=1000)
        # All paragraphs fit in one chunk
        assert len(chunks) >= 1

    def test_empty_text(self):
        assert paragraph_chunks("") == []

    def test_single_paragraph(self):
        chunks = paragraph_chunks("No paragraph breaks here.", chunk_size=1000)
        assert len(chunks) == 1


class TestMarkdownChunks:
    def test_basic_header_splitting(self):
        text = "## Section A\n\nContent A.\n\n## Section B\n\nContent B."
        chunks = markdown_chunks(text, chunk_size=1000)
        full = " ".join(chunks)
        assert "Content A" in full
        assert "Content B" in full

    def test_header_breadcrumb(self):
        text = "## Parent\n\nIntro.\n\n### Child\n\nChild content."
        chunks = markdown_chunks(text, chunk_size=1000)
        child_chunk = [c for c in chunks if "Child content" in c][0]
        assert "## Parent" in child_chunk
        assert "### Child" in child_chunk

    def test_large_section_fallback(self):
        long_content = "Word. " * 200  # ~1200 chars
        text = f"## Big Section\n\n{long_content}"
        chunks = markdown_chunks(text, chunk_size=500)
        assert len(chunks) > 1
        for chunk in chunks:
            assert "## Big Section" in chunk

    def test_small_sections_combined(self):
        text = "## A\n\nShort.\n\n## B\n\nAlso short."
        chunks = markdown_chunks(text, chunk_size=1000)
        assert len(chunks) == 1
        assert "Short" in chunks[0]
        assert "Also short" in chunks[0]

    def test_content_before_first_header(self):
        text = "Preamble paragraph.\n\n## First Header\n\nBody."
        chunks = markdown_chunks(text, chunk_size=1000)
        full = " ".join(chunks)
        assert "Preamble paragraph" in full

    def test_empty_text(self):
        assert markdown_chunks("") == []

    def test_no_headers(self):
        text = "Just plain text with no markdown headers at all."
        chunks = markdown_chunks(text, chunk_size=1000)
        assert len(chunks) == 1
        assert "Just plain text" in chunks[0]

    def test_respects_chunk_size(self):
        sections = "\n\n".join(f"## Section {i}\n\n{'Word ' * 50}" for i in range(10))
        chunks = markdown_chunks(sections, chunk_size=500)
        for chunk in chunks:
            # Allow some overhead for breadcrumb on split sections
            assert len(chunk) < 800

    def test_consecutive_headers_no_crash(self):
        text = "## A\n## B\n## C\n\nContent under C."
        chunks = markdown_chunks(text, chunk_size=1000)
        assert len(chunks) >= 1
        full = " ".join(chunks)
        assert "Content under C" in full

    def test_deeply_nested_headers(self):
        text = "# L1\n\nTop.\n\n## L2\n\nMiddle.\n\n### L3\n\n#### L4\n\nDeep content."
        chunks = markdown_chunks(text, chunk_size=1000)
        deep_chunk = [c for c in chunks if "Deep content" in c][0]
        assert "# L1" in deep_chunk
        assert "#### L4" in deep_chunk


class TestGetChunker:
    def test_fixed_size(self):
        chunker = get_chunker("fixed_size")
        assert chunker is fixed_size_chunks

    def test_sentence(self):
        chunker = get_chunker("sentence")
        assert chunker is sentence_chunks

    def test_paragraph(self):
        chunker = get_chunker("paragraph")
        assert chunker is paragraph_chunks

    def test_markdown(self):
        chunker = get_chunker("markdown")
        assert chunker is markdown_chunks

    def test_unknown_defaults_to_fixed(self):
        chunker = get_chunker("unknown")
        assert chunker is fixed_size_chunks
