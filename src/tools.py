"""
Tool definitions and implementations for the Document Assistant.
Each function maps to a tool that Claude can call.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".py", ".html", ".yaml", ".yml"}


def _resolve(docs_dir: str, filename: str) -> Path:
    """Safely resolve a filename inside docs_dir."""
    base = Path(docs_dir).resolve()
    target = (base / filename).resolve()
    # Security: prevent path traversal
    if not str(target).startswith(str(base)):
        raise ValueError(f"Access denied: {filename} is outside the docs directory.")
    return target


def _all_docs(docs_dir: str) -> list[Path]:
    base = Path(docs_dir)
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(base.glob(f"*{ext}"))
    return sorted(files)


# ── Tool Functions ────────────────────────────────────────────────────────────

def list_documents(docs_dir: str, **kwargs) -> str:
    """List all documents in the docs directory."""
    files = _all_docs(docs_dir)
    if not files:
        return "No documents found. The docs folder is empty."

    lines = ["Available documents:\n"]
    for f in files:
        size = f.stat().st_size
        modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
        lines.append(f"  • {f.name}  [{size_str}]  (modified: {modified})")

    lines.append(f"\nTotal: {len(files)} document(s)")
    return "\n".join(lines)


def read_document(filename: str, docs_dir: str, **kwargs) -> str:
    """Read the full content of a document."""
    # Strip [DOCUMENT: ...] wrapper if present
    filename = filename.strip().lstrip("[").replace("DOCUMENT: ", "").rstrip("]")

    path = _resolve(docs_dir, filename)
    if not path.exists():
        available = [f.name for f in _all_docs(docs_dir)]
        suggestion = f"\nAvailable files: {', '.join(available)}" if available else ""
        return f"Document '{filename}' not found.{suggestion}"

    try:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return f"Document '{filename}' exists but is empty."
        char_count = len(content)
        word_count = len(content.split())
        header = f"── {filename} ({word_count} words, {char_count} chars) ──\n\n"
        return header + content
    except Exception as e:
        return f"Error reading '{filename}': {e}"


def write_document(filename: str, content: str, docs_dir: str, **kwargs) -> str:
    """Create or overwrite a document with the given content."""
    filename = filename.strip().lstrip("[").replace("DOCUMENT: ", "").rstrip("]")

    # Only allow supported extensions
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS and ext != "":
        return f"Unsupported file type '{ext}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"

    path = _resolve(docs_dir, filename)
    action = "Updated" if path.exists() else "Created"
    path.write_text(content, encoding="utf-8")
    word_count = len(content.split())
    return f"✓ {action} '{filename}' ({word_count} words, {len(content)} chars)."


def search_documents(query: str, docs_dir: str, **kwargs) -> str:
    """Search all documents for a keyword or phrase (case-insensitive)."""
    files = _all_docs(docs_dir)
    if not files:
        return "No documents to search."

    query_lower = query.lower()
    results = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            matches = []
            for i, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    matches.append(f"  Line {i}: {line.strip()[:120]}")
            if matches:
                results.append(f"\n📄 {path.name} ({len(matches)} match(es)):")
                results.extend(matches[:5])  # Show max 5 matches per file
                if len(matches) > 5:
                    results.append(f"  … and {len(matches) - 5} more matches")
        except Exception:
            continue

    if not results:
        return f"No matches found for '{query}' across {len(files)} document(s)."

    header = f"Search results for '{query}':\n"
    return header + "\n".join(results)


def summarize_document(filename: str, docs_dir: str, **kwargs) -> str:
    """
    Return a structured summary of a document:
    word count, line count, first 300 chars, and last 100 chars.
    Claude will use this as context to generate a natural language summary.
    """
    filename = filename.strip().lstrip("[").replace("DOCUMENT: ", "").rstrip("]")
    path = _resolve(docs_dir, filename)

    if not path.exists():
        return f"Document '{filename}' not found."

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        words = content.split()

        preview_start = content[:400].strip()
        preview_end   = content[-150:].strip() if len(content) > 400 else ""

        summary = {
            "filename":    filename,
            "word_count":  len(words),
            "line_count":  len(lines),
            "char_count":  len(content),
            "preview_start": preview_start,
            "preview_end":   preview_end,
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error summarizing '{filename}': {e}"


# ── Tool Definitions (for Claude API) ────────────────────────────────────────

def get_tool_definitions() -> list[dict]:
    return [
        {
            "name": "list_documents",
            "description": "List all documents available in the docs directory with their size and modification date.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "read_document",
            "description": "Read the full content of a specific document by filename.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to read, e.g. 'notes.txt' or 'report.md'",
                    }
                },
                "required": ["filename"],
            },
        },
        {
            "name": "write_document",
            "description": "Create a new document or overwrite an existing one with the given content.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to write to, e.g. 'summary.md'",
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write into the document.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
        {
            "name": "search_documents",
            "description": "Search all documents in the directory for a keyword or phrase. Returns matching lines with file name and line number.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The keyword or phrase to search for.",
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "summarize_document",
            "description": "Get metadata and a preview of a document to produce a summary.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to summarize.",
                    }
                },
                "required": ["filename"],
            },
        },
    ]
