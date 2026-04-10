"""Rich display helpers for CLI output — tables, formatters, ASCII art."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

console = Console()

BANNER = (
    "[dim white]  ╔════╗ [/]   [bold cyan]╦ ╦╔═╗╔═╗╦ ╔╦╗╦ ╦[/]  [bold green]╔═╗╔╦╗╦ ╦╔╦╗╦╔═╗[/]   [dim white]╔════╗[/]\n"
    "[dim white]  ║    ║ [/]   [bold cyan]╠═╣║╣ ╠═╣║  ║ ╠═╣[/]  [bold green]╚═╗ ║ ║ ║ ║║║║ ║[/]   [dim white]║    ║[/]\n"
    "[dim white]  ██████ [/]   [bold cyan]╩ ╩╚═╝╩ ╩╩═╝╩ ╩ ╩[/]  [bold green]╚═╝ ╩ ╚═╝═╩╝╩╚═╝[/]   [dim white]██████[/]\n"
    "[dim white]  ██████ [/]                                         [dim white]██████[/]\n"
    "[dim white]   ████  [/]                                          [dim white]████[/]"
)


def print_banner() -> None:
    """Print the ASCII art banner."""
    console.print(BANNER)


def print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    """Print a Rich table with the given title, columns, and rows."""
    table = Table(title=title, show_lines=False)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def print_markdown(text: str) -> None:
    """Render Markdown in the terminal via Rich."""
    md = Markdown(text)
    console.print(md)


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]✓[/green] {message}")
