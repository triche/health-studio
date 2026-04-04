"""Config commands for the Health Studio CLI."""

from __future__ import annotations

import typer
from rich.prompt import Prompt

from health_studio_cli.config import (
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_PATH,
    create_config,
    format_config_for_display,
    read_config,
    set_config_value,
)
from health_studio_cli.display import console, print_error, print_success

app = typer.Typer(help="Manage CLI configuration.")


@app.command()
def init() -> None:
    """Interactive configuration setup."""
    base_url = Prompt.ask("Health Studio base URL", default="http://localhost:8000")
    api_key = Prompt.ask("API key")

    config_file = create_config(
        config_dir=DEFAULT_CONFIG_DIR,
        base_url=base_url,
        api_key=api_key,
    )
    print_success(f"Config saved to {config_file}")


@app.command()
def show() -> None:
    """Show current configuration (API key masked)."""
    try:
        config = read_config()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(code=1) from None

    console.print(format_config_for_display(config))


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Config key (e.g. server.base_url)"),
    value: str = typer.Argument(..., help="New value"),
) -> None:
    """Update a single configuration value."""
    set_config_value(config_path=DEFAULT_CONFIG_PATH, key=key, value=value)
    print_success(f"Updated {key}")
