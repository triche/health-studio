"""Tags commands for the Health Studio CLI."""

from __future__ import annotations

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_table

app = typer.Typer(help="Browse and filter by tags.")

TYPE_STYLES: dict[str, str] = {
    "journal": "[cyan]Journal[/cyan]",
    "goal": "[yellow]Goal[/yellow]",
    "metric_type": "[green]Metric[/green]",
    "exercise_type": "[magenta]Exercise[/magenta]",
}


def _handle_error(e: Exception) -> None:
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
def list_tags() -> None:
    """List all tags with counts."""
    with get_client() as client:
        try:
            response = client.get("/api/tags")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        if not data:
            console.print("[dim]No tags found.[/dim]")
            return

        rows = [[t["tag"], str(t["count"])] for t in data]
        print_table("Tags", ["Tag", "Count"], rows)


@app.command()
def show(
    tag: str = typer.Argument(..., help="Tag name"),
    type_filter: str | None = typer.Option(
        None, "--type", "-t", help="Filter: journal, goal, metric_type, exercise_type"
    ),
) -> None:
    """Show all entities with a given tag."""
    with get_client() as client:
        params: dict[str, str] = {}
        if type_filter:
            params["type"] = type_filter

        try:
            response = client.get(f"/api/tags/{tag}", params=params)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        entities = data.get("entities", [])

        if not entities:
            console.print(f"[dim]No entities tagged '{tag}'.[/dim]")
            return

        rows = []
        for e in entities:
            type_label = TYPE_STYLES.get(e["entity_type"], e["entity_type"])
            rows.append([type_label, e["title"], e["entity_id"][:8]])

        print_table(f"Tag: {tag}", ["Type", "Title", "ID"], rows)
