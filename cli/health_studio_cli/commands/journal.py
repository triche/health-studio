"""Journal commands for the Health Studio CLI."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import (
    console,
    print_error,
    print_markdown,
    print_success,
    print_table,
)
from health_studio_cli.resolve import resolve_id

app = typer.Typer(help="Manage journal entries.")


def _handle_error(e: Exception) -> None:
    """Handle HTTP errors with user-friendly messages."""
    import httpx

    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        print_error(detail)
    else:
        print_error(str(e))
    raise typer.Exit(code=1)


@app.command("list")
def list_entries(
    since: str | None = typer.Option(None, help="Filter entries from this date (YYYY-MM-DD)"),
    limit: int = typer.Option(20, help="Maximum number of entries to return"),
    tag: str | None = typer.Option(None, help="Filter by tag"),
) -> None:
    """List journal entries."""
    with get_client() as client:
        params: dict = {"per_page": limit}
        if since:
            params["date_from"] = since
        if tag:
            params["tag"] = tag
        try:
            response = client.get("/api/journals", params=params)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        items = data.get("items", [])

        if not items:
            console.print("[dim]No journal entries found.[/dim]")
            return

        rows = []
        for item in items:
            rows.append(
                [
                    item["id"][:8],
                    item["entry_date"],
                    item["title"],
                ]
            )

        print_table(
            f"Journal Entries ({data.get('total', len(items))} total)",
            ["ID", "Date", "Title"],
            rows,
        )


@app.command()
def show(journal_id: str = typer.Argument(..., help="Journal entry ID")) -> None:
    """Show a single journal entry with Markdown rendering."""
    with get_client() as client:
        journal_id = resolve_id(client, journal_id, "/api/journals")

        try:
            response = client.get(f"/api/journals/{journal_id}")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        entry = response.json()
        console.print(f"\n[bold]{entry['title']}[/bold]  [dim]{entry['entry_date']}[/dim]\n")
        tags = entry.get("tags", [])
        if tags:
            console.print(f"  Tags: {', '.join(tags)}\n")
        print_markdown(entry["content"])


@app.command()
def create(
    title: str = typer.Option(..., help="Entry title"),
    file: Path | None = typer.Option(None, help="Markdown file to use as entry content"),
    editor: bool = typer.Option(False, help="Open $EDITOR to compose the entry"),
    entry_date: str | None = typer.Option(
        None, "--date", help="Entry date (YYYY-MM-DD, default: today)"
    ),
) -> None:
    """Create a new journal entry."""
    if file and editor:
        print_error("Cannot use both --file and --editor")
        raise typer.Exit(code=1)

    if file:
        content = file.read_text()
    elif editor:
        import os
        import subprocess
        import tempfile

        editor_cmd = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run([editor_cmd, tmp_path], check=True)  # noqa: S603
            content = Path(tmp_path).read_text()
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        print_error("Must provide --file or --editor")
        raise typer.Exit(code=1)

    if not entry_date:
        entry_date = date.today().isoformat()

    with get_client() as client:
        try:
            response = client.post(
                "/api/journals",
                json={"title": title, "content": content, "entry_date": entry_date},
            )
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        entry = response.json()
        print_success(f"Created journal entry: {entry['id']}")
