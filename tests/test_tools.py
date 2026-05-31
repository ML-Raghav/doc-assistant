"""
Unit tests for document tool functions.
Run with: pytest tests/
"""

import os
import pytest
from pathlib import Path
from src.tools import (
    list_documents,
    read_document,
    write_document,
    search_documents,
    summarize_document,
)


@pytest.fixture
def tmp_docs(tmp_path):
    """Create a temporary docs directory with sample files."""
    (tmp_path / "hello.txt").write_text("Hello world\nThis is a test file.\nPython is great.")
    (tmp_path / "notes.md").write_text("# Meeting Notes\n\n- Discuss project timeline\n- Review budget\n- Python setup")
    (tmp_path / "empty.txt").write_text("")
    return str(tmp_path)


# ── list_documents ────────────────────────────────────────────────────────────

def test_list_documents_returns_files(tmp_docs):
    result = list_documents(docs_dir=tmp_docs)
    assert "hello.txt" in result
    assert "notes.md" in result

def test_list_documents_empty(tmp_path):
    result = list_documents(docs_dir=str(tmp_path))
    assert "empty" in result.lower() or "no documents" in result.lower()

def test_list_documents_shows_count(tmp_docs):
    result = list_documents(docs_dir=tmp_docs)
    assert "Total:" in result


# ── read_document ─────────────────────────────────────────────────────────────

def test_read_existing_document(tmp_docs):
    result = read_document(filename="hello.txt", docs_dir=tmp_docs)
    assert "Hello world" in result
    assert "Python is great" in result

def test_read_missing_document(tmp_docs):
    result = read_document(filename="missing.txt", docs_dir=tmp_docs)
    assert "not found" in result.lower()

def test_read_empty_document(tmp_docs):
    result = read_document(filename="empty.txt", docs_dir=tmp_docs)
    assert "empty" in result.lower()

def test_read_shows_word_count(tmp_docs):
    result = read_document(filename="hello.txt", docs_dir=tmp_docs)
    assert "words" in result

def test_read_prevents_path_traversal(tmp_docs):
    with pytest.raises(ValueError, match="Access denied"):
        read_document(filename="../../../etc/passwd", docs_dir=tmp_docs)


# ── write_document ────────────────────────────────────────────────────────────

def test_write_creates_new_file(tmp_docs):
    result = write_document(filename="new_file.txt", content="Created by test", docs_dir=tmp_docs)
    assert "Created" in result
    assert Path(tmp_docs, "new_file.txt").read_text() == "Created by test"

def test_write_overwrites_existing_file(tmp_docs):
    write_document(filename="hello.txt", content="Overwritten content", docs_dir=tmp_docs)
    assert Path(tmp_docs, "hello.txt").read_text() == "Overwritten content"

def test_write_reports_word_count(tmp_docs):
    result = write_document(filename="wc.txt", content="one two three four five", docs_dir=tmp_docs)
    assert "5 words" in result


# ── search_documents ──────────────────────────────────────────────────────────

def test_search_finds_keyword(tmp_docs):
    result = search_documents(query="Python", docs_dir=tmp_docs)
    assert "hello.txt" in result or "notes.md" in result

def test_search_case_insensitive(tmp_docs):
    result = search_documents(query="python", docs_dir=tmp_docs)
    assert "Line" in result  # found something

def test_search_no_results(tmp_docs):
    result = search_documents(query="xyznotfound999", docs_dir=tmp_docs)
    assert "no matches" in result.lower()

def test_search_returns_line_numbers(tmp_docs):
    result = search_documents(query="Hello", docs_dir=tmp_docs)
    assert "Line" in result


# ── summarize_document ────────────────────────────────────────────────────────

def test_summarize_returns_json(tmp_docs):
    import json
    result = summarize_document(filename="hello.txt", docs_dir=tmp_docs)
    data = json.loads(result)
    assert data["filename"] == "hello.txt"
    assert data["word_count"] > 0
    assert "preview_start" in data

def test_summarize_missing_file(tmp_docs):
    result = summarize_document(filename="ghost.txt", docs_dir=tmp_docs)
    assert "not found" in result.lower()
