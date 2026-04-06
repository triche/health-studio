"""Import commands for the Health Studio CLI."""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 — Typer needs this at runtime

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import print_error, print_success, print_table

app = typer.Typer(help="Import data into Health Studio.")


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
def import_json(
    input_file: Path = typer.Argument(..., help="JSON backup file to import"),
) -> None:
    """Import a full JSON backup."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(code=1)

    data = json.loads(input_file.read_text())

    with get_client() as client:
        try:
            response = client.post("/api/import/json", json=data)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        result = response.json()
        rows = [[k, str(v)] for k, v in result.items()]
        print_table("Import Results", ["Entity", "Count"], rows)


@app.command("csv")
def import_csv(
    entity: str = typer.Argument(..., help="Entity type: metric_entries, result_entries"),
    input_file: Path = typer.Argument(..., help="CSV file to import"),
) -> None:
    """Import CSV data for metrics or results."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(code=1)

    content = input_file.read_bytes()

    with get_client() as client:
        try:
            response = client.post(
                f"/api/import/csv/{entity}",
                files={"file": (input_file.name, content, "text/csv")},
            )
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        result = response.json()
        print_success(f"Imported {result.get('imported', 0)} rows into {entity}")
