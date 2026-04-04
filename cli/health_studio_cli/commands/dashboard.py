"""Dashboard command for the Health Studio CLI."""

from __future__ import annotations

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_table

app = typer.Typer(help="View dashboard summary.")


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


@app.callback(invoke_without_command=True)
def dashboard() -> None:
    """Show a compact dashboard summary."""
    with get_client() as client:
        try:
            response = client.get("/api/dashboard/summary")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()

        # Recent Journals
        journals = data.get("recent_journals", [])
        if journals:
            rows = [[j["entry_date"], j["title"]] for j in journals]
            print_table("Recent Journal Entries", ["Date", "Title"], rows)

        # Active Goals
        goals = data.get("active_goals", [])
        if goals:
            rows = [[g["title"], f"{g.get('progress', 0):.0f}%"] for g in goals]
            print_table("Active Goals", ["Title", "Progress"], rows)

        # Latest Metrics
        metrics = data.get("latest_metrics", [])
        if metrics:
            rows = []
            for m in metrics:
                val = m["value"]
                unit = m.get("unit", "")
                if unit == "minutes" and val >= 60:
                    hours = int(val // 60)
                    mins = int(val % 60)
                    display = f"{hours}h {mins}m"
                else:
                    display = f"{val:.1f}"
                rows.append([m["metric_name"], display, m.get("unit", ""), m["recorded_date"]])
            print_table("Latest Metrics", ["Metric", "Value", "Unit", "Date"], rows)

        # Recent PRs
        prs = data.get("recent_prs", [])
        if prs:
            rows = [
                [
                    p["exercise_name"],
                    f"{p['value']:.1f}",
                    p.get("result_unit", ""),
                    p["recorded_date"],
                ]
                for p in prs
            ]
            print_table("Recent PRs 🏆", ["Exercise", "Value", "Unit", "Date"], rows)

        if not any([journals, goals, metrics, prs]):
            console.print("[dim]No data yet. Start tracking![/dim]")
