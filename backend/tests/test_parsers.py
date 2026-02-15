"""Tests for document parsers."""
import json
import os
import tempfile

import pytest

from app.utils.parsers import (
    _extract_frontmatter,
    parse_txt,
    parse_csv,
    parse_json,
    parse_markdown,
    parse_document,
)


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


def _parse_md(content: str) -> str:
    """Helper: write markdown content to a temp file and parse it."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        path = f.name
    try:
        return parse_markdown(path)
    finally:
        os.unlink(path)


class TestExtractFrontmatter:
    def test_basic_frontmatter(self):
        text = "---\ntitle: Test\nauthor: Bob\n---\n\nBody text."
        body, meta = _extract_frontmatter(text)
        assert meta["title"] == "Test"
        assert meta["author"] == "Bob"
        assert "Body text" in body
        assert "title:" not in body

    def test_no_frontmatter(self):
        text = "# Just a heading\n\nSome text."
        body, meta = _extract_frontmatter(text)
        assert body == text
        assert meta == {}

    def test_frontmatter_with_dashes_in_body(self):
        text = "---\ntitle: Test\n---\n\nSome text with --- dashes."
        body, meta = _extract_frontmatter(text)
        assert "---" in body
        assert meta["title"] == "Test"


class TestMarkdownParser:
    def test_parse_markdown(self):
        result = _parse_md("# Title\n\nSome **bold** text and *italic* text.")
        assert "Title" in result
        assert "bold" in result
        assert "**" not in result

    def test_code_blocks_preserved(self):
        md = "# Title\n\n```python\ndef hello():\n    print('hi')\n```\n\nAfter code."
        result = _parse_md(md)
        assert "def hello():" in result
        assert "print('hi')" in result
        assert "After code" in result

    def test_inline_code_preserved(self):
        result = _parse_md("Use the `print()` function.")
        assert "print()" in result

    def test_tables_parsed(self):
        md = "| Name | Age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
        result = _parse_md(md)
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result

    def test_links_text_preserved(self):
        result = _parse_md("Visit [OpenAI](https://openai.com) for more.")
        assert "OpenAI" in result

    def test_blockquotes(self):
        result = _parse_md("> This is a quote.")
        assert "This is a quote" in result

    def test_nested_formatting(self):
        result = _parse_md("This has **bold with *nested italic* inside** it.")
        assert "bold" in result
        assert "nested italic" in result
        assert "**" not in result

    def test_ordered_list(self):
        result = _parse_md("1. First\n2. Second\n3. Third")
        assert "First" in result
        assert "Second" in result

    def test_unordered_list(self):
        result = _parse_md("- Item A\n- Item B")
        assert "Item A" in result
        assert "Item B" in result

    def test_frontmatter_stripped(self):
        md = "---\ntitle: My Doc\nauthor: Alice\n---\n\n# Heading\n\nBody text."
        result = _parse_md(md)
        assert "title:" not in result
        assert "Heading" in result
        assert "Body text" in result

    def test_header_markers_preserved(self):
        md = "## Section One\n\nContent here.\n\n### Subsection\n\nMore content."
        result = _parse_md(md)
        assert "## Section One" in result
        assert "### Subsection" in result

    def test_empty_file(self):
        result = _parse_md("")
        assert result.strip() == ""

    def test_code_block_indented(self):
        md = "```\n# comment in code\nprint('hi')\n```"
        result = _parse_md(md)
        # Code block content should be indented so # is not at line start
        for line in result.splitlines():
            if "# comment" in line:
                assert line.startswith("    ")


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
