"""Goals commands for the Health Studio CLI."""

from __future__ import annotations

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_markdown, print_table
from health_studio_cli.resolve import resolve_id

app = typer.Typer(help="Track goals and progress.")


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
def list_goals(
    status: str | None = typer.Option(None, help="Filter by status: active, completed, abandoned"),
    tag: str | None = typer.Option(None, help="Filter by tag"),
) -> None:
    """List goals."""
    with get_client() as client:
        params: dict = {}
        if status:
            params["status"] = status
        if tag:
            params["tag"] = tag

        try:
            response = client.get("/api/goals", params=params)
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        data = response.json()
        items = data.get("items", [])

        if not items:
            console.print("[dim]No goals found.[/dim]")
            return

        rows = []
        for goal in items:
            progress = goal.get("progress", 0)
            rows.append(
                [
                    goal["id"][:8],
                    goal["title"],
                    goal["status"],
                    f"{progress:.0f}%",
                    goal.get("deadline") or "—",
                ]
            )

        print_table(
            f"Goals ({data.get('total', len(items))} total)",
            ["ID", "Title", "Status", "Progress", "Deadline"],
            rows,
        )


@app.command()
def show(goal_id: str = typer.Argument(..., help="Goal ID")) -> None:
    """Show goal detail with progress."""
    with get_client() as client:
        goal_id = resolve_id(client, goal_id, "/api/goals")

        try:
            response = client.get(f"/api/goals/{goal_id}")
            response.raise_for_status()
        except Exception as e:
            _handle_error(e)

        goal = response.json()
        progress = goal.get("progress", 0)
        direction = "↓ Lower is better" if goal.get("lower_is_better") else "↑ Higher is better"

        console.print(f"\n[bold]{goal['title']}[/bold]  [{goal['status']}]")
        console.print(f"  {direction}")
        console.print(f"  Progress: {progress:.1f}%")

        if goal.get("start_value") is not None:
            console.print(f"  Start: {goal['start_value']}")
        console.print(f"  Current: {goal.get('current_value', '—')}")
        console.print(f"  Target: {goal['target_value']}")

        if goal.get("deadline"):
            console.print(f"  Deadline: {goal['deadline']}")

        tags = goal.get("tags", [])
        if tags:
            console.print(f"  Tags: {', '.join(tags)}")

        if goal.get("description"):
            console.print(f"\n{goal['description']}")

        if goal.get("plan"):
            console.print("\n[bold]Plan:[/bold]")
            print_markdown(goal["plan"])
