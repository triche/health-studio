"""Export commands for the Health Studio CLI."""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 — Typer needs this at runtime

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import print_error, print_success

app = typer.Typer(help="Export Health Studio data.")


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


@app.command("json")
def export_json(
    output: Path = typer.Argument(..., help="Output file path (.json)"),
) -> None:
    """Export all data as a JSON backup."""
    with get_client() as client:
        try:
            response = client.get("/api/export/json")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, indent=2))
        print_success(f"Exported JSON backup to {output}")


@app.command("csv")
def export_csv(
    entity: str = typer.Argument(
        ...,
        help="Entity: metric_types, metric_entries, "
        "exercise_types, result_entries, journal_entries, goals",
    ),
    output: Path = typer.Argument(..., help="Output file path (.csv)"),
) -> None:
    """Export a single entity type as CSV."""
    with get_client() as client:
        try:
            response = client.get(f"/api/export/csv/{entity}")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response.text)
        print_success(f"Exported {entity} CSV to {output}")


@app.command("markdown")
def export_markdown(
    output: Path = typer.Argument(..., help="Output file path (.md)"),
) -> None:
    """Export journal entries as Markdown."""
    with get_client() as client:
        try:
            response = client.get("/api/export/journals/markdown")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response.text)
        print_success(f"Exported journals Markdown to {output}")
