"""Metrics commands for the Health Studio CLI."""

from __future__ import annotations

from datetime import date

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_success, print_table
from health_studio_cli.resolve import resolve_id

app = typer.Typer(help="Track health metrics.")


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


@app.command()
def types() -> None:
    """List available metric types."""
    with get_client() as client:
        try:
            response = client.get("/api/metric-types")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        if not data:
            console.print("[dim]No metric types found.[/dim]")
            return

        rows = []
        for mt in data:
            rows.append([mt["id"][:8], mt["name"], mt["unit"]])

        print_table("Metric Types", ["ID", "Name", "Unit"], rows)


@app.command()
def log(
    type_id: str = typer.Argument(..., help="Metric type ID"),
    value: float = typer.Argument(..., help="Metric value"),
    log_date: str | None = typer.Option(None, "--date", help="Date (YYYY-MM-DD, default: today)"),
    notes: str | None = typer.Option(None, help="Optional notes"),
) -> None:
    """Log a metric entry."""
    if not log_date:
        log_date = date.today().isoformat()

    with get_client() as client:
        type_id = resolve_id(client, type_id, "/api/metric-types")

        body: dict = {
            "metric_type_id": type_id,
            "value": value,
            "recorded_date": log_date,
        }
        if notes:
            body["notes"] = notes

        try:
            response = client.post("/api/metrics", json=body)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        entry = response.json()
        print_success(f"Logged metric entry: {entry['id']}")


@app.command()
def trend(
    type_id: str = typer.Argument(..., help="Metric type ID"),
    since: str | None = typer.Option(None, help="Start date (YYYY-MM-DD)"),
) -> None:
    """Show trend data for a metric type."""
    with get_client() as client:
        type_id = resolve_id(client, type_id, "/api/metric-types")

        params: dict = {}
        if since:
            params["date_from"] = since

        try:
            response = client.get(f"/api/metrics/trends/{type_id}", params=params)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        points = data.get("data", [])

        if not points:
            console.print("[dim]No trend data available.[/dim]")
            return

        title = f"{data.get('metric_name', 'Metric')} ({data.get('unit', '')})"
        rows = []
        for pt in points:
            rows.append([pt["recorded_date"], f"{pt['value']:.1f}"])

        print_table(title, ["Date", "Value"], rows)
