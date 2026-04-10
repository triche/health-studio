"""Health Studio CLI — main Typer application."""

from __future__ import annotations

import typer

from health_studio_cli.commands.config_cmd import app as config_app
from health_studio_cli.commands.dashboard import app as dashboard_app
from health_studio_cli.commands.export_cmd import app as export_app
from health_studio_cli.commands.goals import app as goals_app
from health_studio_cli.commands.import_cmd import app as import_app
from health_studio_cli.commands.journal import app as journal_app
from health_studio_cli.commands.metrics import app as metrics_app
from health_studio_cli.commands.results import app as results_app
from health_studio_cli.commands.search import app as search_app
from health_studio_cli.commands.tags import app as tags_app
from health_studio_cli.commands.timeline import app as timeline_app
from health_studio_cli.display import BANNER, console

__version__ = "0.1.0"

app = typer.Typer(
    name="hs",
    help="Health Studio CLI — command-line interface for the Health Studio API.",
    invoke_without_command=True,
    no_args_is_help=False,
)

app.add_typer(journal_app, name="journal")
app.add_typer(metrics_app, name="metrics")
app.add_typer(results_app, name="results")
app.add_typer(goals_app, name="goals")
app.add_typer(config_app, name="config")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.add_typer(search_app, name="search")
app.add_typer(tags_app, name="tags")
app.add_typer(timeline_app, name="timeline")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"Health Studio CLI v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version.", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Health Studio CLI."""
    if ctx.invoked_subcommand is None:
        console.print(BANNER, style="bold cyan")
        console.print(f"\nHealth Studio CLI v{__version__}")
        console.print("Run [bold]hs --help[/bold] for usage information.\n")
