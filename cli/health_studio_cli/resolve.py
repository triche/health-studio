"""Resolve truncated ID prefixes to full UUIDs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from health_studio_cli.display import print_error

if TYPE_CHECKING:
    import httpx

# Standard UUID length with hyphens: 36 chars (8-4-4-4-12)
_FULL_UUID_LENGTH = 36


def resolve_id(client: httpx.Client, short_id: str, list_endpoint: str) -> str:
    """Resolve a (possibly truncated) ID prefix to a full UUID.

    If *short_id* is already a full UUID (36 chars), it is returned as-is
    without any network call.  Otherwise the *list_endpoint* is fetched to
    find exactly one record whose ``id`` starts with *short_id*.

    Exits with an error when zero or multiple records match.
    """
    if len(short_id) == _FULL_UUID_LENGTH:
        return short_id

    response = client.get(list_endpoint)
    response.raise_for_status()

    data = response.json()
    # Support both flat lists and paginated responses with "items" key
    items = data if isinstance(data, list) else data.get("items", [])

    matches = [item for item in items if item["id"].startswith(short_id)]

    if len(matches) == 1:
        return matches[0]["id"]

    if len(matches) == 0:
        print_error(f"No match for ID prefix '{short_id}'")
    else:
        names = ", ".join(m.get("name") or m.get("title") or m["id"][:8] for m in matches)
        print_error(f"Ambiguous ID prefix '{short_id}' — matches: {names}")

    raise typer.Exit(code=1)
