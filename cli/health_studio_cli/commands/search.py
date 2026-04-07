"""Search command for the Health Studio CLI."""

from __future__ import annotations

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_table

app = typer.Typer(help="Search across all health data.")


TYPE_STYLES: dict[str, str] = {
    "journal": "[cyan]Journal[/cyan]",
    "goal": "[yellow]Goal[/yellow]",
    "metric_type": "[green]Metric[/green]",
    "exercise_type": "[magenta]Exercise[/magenta]",
}


@app.callback(invoke_without_command=True)
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query"),
    type_filter: str | None = typer.Option(
        None, "--type", "-t", help="Filter by type: journal, goal, metric, exercise"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Search across journals, goals, metrics, and exercise types."""
    # Map friendly type names to API entity types
    type_map = {
        "journal": "journal",
        "goal": "goal",
        "metric": "metric_type",
        "exercise": "exercise_type",
    }

    with get_client() as client:
        params: dict[str, str | int] = {"q": query, "limit": limit}
        if type_filter:
            mapped = type_map.get(type_filter, type_filter)
            params["types"] = mapped

        try:
            response = client.get("/api/search", params=params)
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
        results = data.get("results", [])

        if not results:
            console.print(f"[dim]No results for '{query}'.[/dim]")
            return

        rows = []
        for r in results:
            type_label = TYPE_STYLES.get(r["entity_type"], r["entity_type"])
            # Strip HTML mark tags for terminal display
            snippet = r.get("snippet", "").replace("<mark>", "").replace("</mark>", "")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            rows.append([type_label, r["title"], snippet])

        print_table(
            f"Search: '{query}' ({data.get('total', len(results))} results)",
            ["Type", "Title", "Snippet"],
            rows,
        )
