"""
Agentic Document Assistant
--------------------------
A CLI-based chatbot that lets you interact with local documents
using natural language. Powered by Claude API.

Usage:
    python src/assistant.py
    python src/assistant.py --docs_dir my_documents/
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

from tools import (
    read_document,
    write_document,
    search_documents,
    list_documents,
    summarize_document,
    get_tool_definitions,
)

load_dotenv()
console = Console()

SYSTEM_PROMPT = """You are an intelligent document assistant. You help users read, search, write, and manage local documents through natural language.

You have access to the following tools:
- list_documents   : List all available documents in the docs directory
- read_document    : Read the full content of a specific document
- search_documents : Search across all documents for a keyword or phrase
- write_document   : Create or update a document with given content
- summarize_document: Get a concise summary of a document

Guidelines:
- When a user uses @filename (e.g. @notes.txt), always read that document first
- When a user types /list, use list_documents immediately
- When a user types /search <term>, use search_documents immediately
- When a user types /summarize @filename, summarize that document
- When a user types /write @filename <content>, write to that document
- Be concise and helpful. Always cite which document you got information from.
- If a document doesn't exist, say so clearly and offer to create it.
"""


class DocumentAssistant:
    def __init__(self, docs_dir: str = "docs"):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(exist_ok=True)
        self.conversation_history = []
        self.tool_definitions = get_tool_definitions()

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Route tool calls to the appropriate function."""
        tool_input["docs_dir"] = str(self.docs_dir)

        dispatch = {
            "list_documents":    list_documents,
            "read_document":     read_document,
            "search_documents":  search_documents,
            "write_document":    write_document,
            "summarize_document": summarize_document,
        }

        fn = dispatch.get(tool_name)
        if fn:
            return fn(**tool_input)
        return f"Unknown tool: {tool_name}"

    def _preprocess_input(self, user_input: str) -> str:
        """Expand @mentions and /commands into natural language for Claude."""
        # @filename → "please read the document named filename"
        user_input = re.sub(
            r"@([\w.\-]+)",
            r"[DOCUMENT: \1]",
            user_input
        )
        return user_input

    def chat(self, user_message: str) -> str:
        """Send a message and get a response, handling tool use."""
        processed = self._preprocess_input(user_message)
        self.conversation_history.append({"role": "user", "content": processed})

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self.tool_definitions,
                messages=self.conversation_history,
            )

            # If Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Add assistant's response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Process each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        console.print(f"  [dim]⚙ Using tool: [cyan]{block.name}[/cyan] {block.input}[/dim]")
                        result = self._handle_tool_call(block.name, dict(block.input))
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Add tool results to history
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results,
                })
                # Loop — Claude will now generate a final response

            else:
                # Final text response
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_text,
                })
                return final_text

    def run(self):
        """Start the interactive CLI session."""
        console.print(Panel.fit(
            "[bold cyan]📄 Agentic Document Assistant[/bold cyan]\n"
            "[dim]Powered by Claude · Type [bold]/help[/bold] for commands · [bold]/quit[/bold] to exit[/dim]",
            border_style="cyan"
        ))
        console.print(f"[dim]Watching docs in:[/dim] [green]{self.docs_dir.resolve()}[/green]\n")

        while True:
            try:
                user_input = Prompt.ask("[bold blue]You[/bold blue]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            if not user_input:
                continue

            if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
                console.print("[yellow]Goodbye![/yellow]")
                break

            if user_input.lower() == "/help":
                self._show_help()
                continue

            if user_input.lower() == "/clear":
                self.conversation_history = []
                console.print("[green]Conversation cleared.[/green]")
                continue

            if user_input.lower() == "/history":
                self._show_history()
                continue

            with console.status("[bold green]Thinking…[/bold green]", spinner="dots"):
                try:
                    response = self.chat(user_input)
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    continue

            console.print()
            console.print(Panel(
                Markdown(response),
                title="[bold green]Assistant[/bold green]",
                border_style="green",
                padding=(0, 1),
            ))
            console.print()

    def _show_help(self):
        table = Table(title="Available Commands", border_style="cyan", show_header=True)
        table.add_column("Command", style="bold cyan", width=28)
        table.add_column("Description")

        commands = [
            ("/list",                      "List all documents in the docs folder"),
            ("/search <term>",             "Search all documents for a term"),
            ("/summarize @filename",       "Summarize a specific document"),
            ("/write @filename <content>", "Write content to a document"),
            ("@filename",                  "Reference a document inline (e.g. what is @notes.txt about?)"),
            ("/clear",                     "Clear conversation history"),
            ("/history",                   "Show conversation history length"),
            ("/help",                      "Show this help message"),
            ("/quit",                      "Exit the assistant"),
        ]
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        console.print(table)
        console.print()

    def _show_history(self):
        n = len([m for m in self.conversation_history if isinstance(m.get("content"), str)])
        console.print(f"[dim]Conversation has [cyan]{n}[/cyan] messages.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="Agentic Document Assistant powered by Claude")
    parser.add_argument("--docs_dir", default="docs", help="Path to documents directory (default: docs/)")
    args = parser.parse_args()

    assistant = DocumentAssistant(docs_dir=args.docs_dir)
    assistant.run()


if __name__ == "__main__":
    main()
