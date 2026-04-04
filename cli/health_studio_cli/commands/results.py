"""Results commands for the Health Studio CLI."""

from __future__ import annotations

from datetime import date

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_success, print_table

app = typer.Typer(help="Track exercise results and PRs.")


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
    """List available exercise types."""
    with get_client() as client:
        try:
            response = client.get("/api/exercise-types")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        if not data:
            console.print("[dim]No exercise types found.[/dim]")
            return

        rows = []
        for et in data:
            rows.append([et["id"][:8], et["name"], et["category"], et["result_unit"]])

        print_table("Exercise Types", ["ID", "Name", "Category", "Unit"], rows)


@app.command()
def log(
    exercise_id: str = typer.Argument(..., help="Exercise type ID"),
    value: float = typer.Argument(..., help="Result value"),
    log_date: str | None = typer.Option(None, "--date", help="Date (YYYY-MM-DD, default: today)"),
    notes: str | None = typer.Option(None, help="Optional notes"),
) -> None:
    """Log an exercise result."""
    if not log_date:
        log_date = date.today().isoformat()

    body: dict = {
        "exercise_type_id": exercise_id,
        "value": value,
        "recorded_date": log_date,
    }
    if notes:
        body["notes"] = notes

    with get_client() as client:
        try:
            response = client.post("/api/results", json=body)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        entry = response.json()
        pr_badge = " 🏆 PR!" if entry.get("is_pr") else ""
        print_success(f"Logged result: {entry['id']}{pr_badge}")


@app.command()
def prs(
    exercise_id: str = typer.Argument(..., help="Exercise type ID"),
) -> None:
    """Show PR history for an exercise."""
    with get_client() as client:
        try:
            response = client.get(f"/api/results/prs/{exercise_id}")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        if not data:
            console.print("[dim]No PRs found.[/dim]")
            return

        rows = []
        for entry in data:
            rx = "✓" if entry.get("is_rx") else ""
            rows.append(
                [
                    entry["recorded_date"],
                    f"{entry['value']:.1f}",
                    rx,
                    entry.get("notes") or "",
                ]
            )

        print_table("Personal Records", ["Date", "Value", "RX", "Notes"], rows)
