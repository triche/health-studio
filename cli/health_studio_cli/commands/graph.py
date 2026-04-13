"""Graph command for the Health Studio CLI."""

from __future__ import annotations

from collections import Counter

import typer

from health_studio_cli.api import get_client
from health_studio_cli.display import console, print_error, print_table

app = typer.Typer(help="View graph statistics about entity connections.")


@app.callback(invoke_without_command=True)
def graph(ctx: typer.Context) -> None:
    """Show graph statistics — connection counts, most connected entities, orphans."""
    if ctx.invoked_subcommand is not None:
        return

    with get_client() as client:
        try:
            response = client.get("/api/graph", params={"include_orphans": "true"})
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
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        if not nodes:
            console.print("[dim]No entities found in graph.[/dim]")
            return

        # Count connections per node
        connection_count: Counter[str] = Counter()
        for edge in edges:
            connection_count[edge["source"]] += 1
            connection_count[edge["target"]] += 1

        node_map = {n["id"]: n for n in nodes}

        # Summary stats
        type_counts = Counter(n["type"] for n in nodes)
        edge_type_counts = Counter(e["type"] for e in edges)
        orphan_count = sum(1 for n in nodes if connection_count[n["id"]] == 0)

        console.print("\n[bold]Graph Summary[/bold]")
        console.print(f"  Nodes: [cyan]{len(nodes)}[/cyan]  Edges: [cyan]{len(edges)}[/cyan]  Orphans: [yellow]{orphan_count}[/yellow]")

        # Node type breakdown
        type_rows = []
        for t, count in sorted(type_counts.items()):
            type_rows.append([t, str(count)])
        print_table("Nodes by Type", ["Type", "Count"], type_rows)

        # Edge type breakdown
        if edges:
            edge_rows = []
            for t, count in sorted(edge_type_counts.items()):
                edge_rows.append([t, str(count)])
            print_table("Edges by Type", ["Type", "Count"], edge_rows)

        # Most connected entities (top 10)
        if connection_count:
            top = connection_count.most_common(10)
            top_rows = []
            for nid, count in top:
                node = node_map.get(nid, {})
                label = node.get("label", nid)
                ntype = node.get("type", "unknown")
                top_rows.append([label, ntype, str(count)])
            print_table("Most Connected", ["Entity", "Type", "Connections"], top_rows)
