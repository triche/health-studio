"""Timeline command for the Health Studio CLI."""

from __future__ import annotations

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_table

app = typer.Typer(help="View a unified timeline of health data.")

TYPE_STYLES: dict[str, str] = {
    "journal": "[cyan]📓 Journal[/cyan]",
    "metric": "[green]📊 Metric[/green]",
    "result": "[magenta]🏋️ Result[/magenta]",
    "goal": "[yellow]🎯 Goal[/yellow]",
}


@app.callback(invoke_without_command=True)
def timeline(
    ctx: typer.Context,
    type_filter: str | None = typer.Option(
        None, "--type", "-t", help="Comma-separated types: journal,metric,result,goal"
    ),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum items"),
) -> None:
    """Show a chronological timeline of health data."""
    with get_client() as client:
        params: dict[str, str | int] = {"per_page": limit}
        if type_filter:
            params["types"] = type_filter
        if tag:
            params["tag"] = tag

        try:
            response = client.get("/api/timeline", params=params)
            response.raise_for_status()
        except Exception as e:
            import httpx

            if isinstance(e, httpx.HTTPStatusError):
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                print_error(detail)
            else:
                print_error(str(e))
            raise typer.Exit(code=1) from None

        data = response.json()
        items = data.get("items", [])

        if not items:
            console.print("[dim]No timeline entries found.[/dim]")
            return

        rows = []
        for item in items:
            type_label = TYPE_STYLES.get(item["type"], item["type"])
            summary = item.get("summary", "")
            if len(summary) > 60:
                summary = summary[:57] + "..."
            rows.append([item["date"], type_label, item["title"], summary])

        print_table(
            f"Timeline ({data.get('total', len(items))} items)",
            ["Date", "Type", "Title", "Summary"],
            rows,
        )
