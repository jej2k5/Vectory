"""Tests for document parsers."""
import json
import os
import tempfile

import pytest

from app.utils.parsers import parse_txt, parse_csv, parse_json, parse_markdown, parse_document


class TestTxtParser:
    def test_parse_txt(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello World\nLine 2")
            f.flush()
            result = parse_txt(f.name)
            assert "Hello World" in result
            assert "Line 2" in result
            os.unlink(f.name)


class TestCsvParser:
    def test_parse_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,age\nAlice,30\nBob,25")
            f.flush()
            result = parse_csv(f.name)
            assert "Alice" in result
            assert "Bob" in result
            os.unlink(f.name)


class TestJsonParser:
    def test_parse_json(self):
        data = {"name": "Test", "items": [1, 2, 3]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            result = parse_json(f.name)
            assert "Test" in result
            os.unlink(f.name)


class TestMarkdownParser:
    def test_parse_markdown(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\nSome **bold** text and *italic* text.")
            f.flush()
            result = parse_markdown(f.name)
            assert "Title" in result
            assert "bold" in result
            assert "**" not in result
            os.unlink(f.name)


class TestParseDocument:
    def test_parse_txt_document(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            f.flush()
            result = parse_document(f.name, "txt")
            assert result == "test content"
            os.unlink(f.name)

    def test_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document("/tmp/test.xyz", "xyz")
