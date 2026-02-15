"""Tests for text chunking utilities."""
import pytest

from app.utils.chunking import (
    fixed_size_chunks,
    sentence_chunks,
    paragraph_chunks,
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

    def test_unknown_defaults_to_fixed(self):
        chunker = get_chunker("unknown")
        assert chunker is fixed_size_chunks
