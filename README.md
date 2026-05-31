# 📄 Agentic Document Assistant

> A CLI-based AI agent that lets you interact with your local documents using natural language.  
> Powered by **Claude API** with agentic tool use.  
> Author: **Raghav Patidar** · [GitHub](https://github.com/ML-Raghav) · [LinkedIn](https://linkedin.com/in/raghav-patidar2)

---

## What It Does

Instead of manually opening files, this assistant lets you talk to your documents:

```
You > What are the action items in @meeting_notes.md?
You > /search transformer
You > Summarize @ml_notes.txt
You > /write @todo.md - Review roadmap\n- Submit PR by Friday
```

Claude reads the right files, searches across them, and responds with accurate, grounded answers — no hallucination from memory, always from your actual documents.

---

## Features

| Feature | Description |
|---------|-------------|
| `@mention` injection | Reference any file inline — Claude reads it automatically |
| `/slash commands` | Fast dispatch: `/list`, `/search`, `/summarize`, `/write` |
| **Agentic tool loop** | Claude decides which tools to call and chains them if needed |
| **5 built-in tools** | `read`, `write`, `search`, `list`, `summarize` |
| **Path traversal guard** | Sandboxes all file access within the docs directory |
| **Rich terminal UI** | Markdown rendering, spinner, colored panels |
| **Conversation memory** | Full multi-turn context across the session |

---

## Demo

```
╭──────────────────────────────────────────╮
│  📄 Agentic Document Assistant            │
│  Powered by Claude · /help · /quit        │
╰──────────────────────────────────────────╯
Watching docs in: /home/raghav/doc-assistant/docs

You > /list
  ⚙ Using tool: list_documents
╭─ Assistant ─────────────────────────────────╮
│ Available documents:                         │
│  • meeting_notes.md  [1.1 KB]                │
│  • ml_notes.txt  [892 bytes]                 │
│  • project_roadmap.md  [1.4 KB]              │
│ Total: 3 document(s)                         │
╰──────────────────────────────────────────────╯

You > What are the action items in @meeting_notes.md?
  ⚙ Using tool: read_document {"filename": "meeting_notes.md"}
╭─ Assistant ─────────────────────────────────╮
│ From **meeting_notes.md**, the action items: │
│ - Raghav: Set up project structure           │
│ - Raghav: Implement tool functions + tests   │
│ - Team Lead: Review API usage & costs        │
│ - PM: Define sample use cases for demo       │
╰──────────────────────────────────────────────╯
```

---

## Project Structure

```
doc-assistant/
├── src/
│   ├── assistant.py       # Main CLI agent + conversation loop
│   └── tools.py           # Tool implementations + Claude tool definitions
├── tests/
│   └── test_tools.py      # 17 unit tests (all passing)
├── docs/                  # Your local documents go here
│   ├── meeting_notes.md
│   ├── ml_notes.txt
│   └── project_roadmap.md
├── .env.example           # API key template
├── requirements.txt
└── README.md
```

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/ML-Raghav/doc-assistant.git
cd doc-assistant
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Set API Key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
# Get one free at: https://console.anthropic.com/
```

### 4. Run

```bash
python src/assistant.py

# Custom docs folder:
python src/assistant.py --docs_dir ~/my-notes/
```

---

## Commands Reference

| Command | What it does |
|---------|-------------|
| `@filename` | Inject a document into context, e.g. *"explain @ml_notes.txt"* |
| `/list` | Show all documents with size and modification date |
| `/search <term>` | Search all docs for a keyword, returns matching lines |
| `/summarize @filename` | Get a summary of a document |
| `/write @filename <text>` | Create or update a document |
| `/clear` | Clear conversation history |
| `/history` | Show message count in current session |
| `/help` | Show command reference |
| `/quit` | Exit |

---

## How It Works

```
User Input
    │
    ▼
Preprocess (@mentions, /commands)
    │
    ▼
Claude API (claude-sonnet) ◄──── System Prompt + Conversation History
    │
    ├── stop_reason = "tool_use" ──► Execute Tool ──► Return Result ──┐
    │                                                                   │
    └── stop_reason = "end_turn" ◄──────────────────────────────────┘
    │
    ▼
Render response with Rich Markdown
```

Claude autonomously decides which tools to invoke. For complex queries it chains multiple tool calls before producing a final answer.

---

## Tools

### `read_document(filename)`
Reads full content of a file. Returns word count, character count, and content.

### `write_document(filename, content)`
Creates or overwrites a file. Path-sandboxed to docs directory.

### `search_documents(query)`
Case-insensitive search across all documents. Returns file name, line numbers, and matching lines.

### `list_documents()`
Lists all `.txt`, `.md`, `.json`, `.csv`, `.py` files with size and last-modified date.

### `summarize_document(filename)`
Returns structured metadata (word count, line count, preview) — Claude generates a natural language summary from this.

---

## Tests

```bash
pytest tests/ -v
# 17 passed in 0.06s
```

Tests cover: list, read, write, search, summarize — including edge cases like missing files, empty files, and path traversal attempts.

---

## Tech Stack

- **Python 3.11+**
- **Anthropic Claude API** — `claude-sonnet-4` with tool use
- **Rich** — Terminal UI (markdown, panels, spinners, tables)
- **python-dotenv** — Environment variable management
- **pytest** — Unit testing

---

## License

MIT — free to use and build on.

---

*Part of my NLP/LLM portfolio. Connect on [LinkedIn](https://linkedin.com/in/raghav-patidar2) or check out my other projects on [GitHub](https://github.com/ML-Raghav).*
