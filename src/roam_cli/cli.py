from __future__ import annotations

import json
import sys

import click

from .config import get_db_path, get_roam_dir, interactive_config, save_config
from .db import RoamDB
from .search import fuzzy_search


def _output(data, fmt: str) -> None:
    if fmt == "json":
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        # Simple table-ish output
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    click.echo("---")
                    for k, v in item.items():
                        click.echo(f"  {k}: {v}")
                else:
                    click.echo(item)
        elif isinstance(data, dict):
            for k, v in data.items():
                click.echo(f"{k}: {v}")
        else:
            click.echo(data)


@click.group()
@click.option("--db", "db_path", default=None, help="Override database path")
@click.option("--roam-dir", default=None, help="Override org-roam root directory")
@click.option("--workspace", "-w", default=None, help="Workspace subdirectory filter")
@click.option("--format", "fmt", type=click.Choice(["json", "table"]), default="json", help="Output format")
@click.pass_context
def cli(ctx, db_path, roam_dir, workspace, fmt):
    """CLI tool for querying org-roam databases."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = get_db_path(db_path)
    ctx.obj["roam_dir"] = get_roam_dir(roam_dir)
    ctx.obj["workspace"] = workspace
    ctx.obj["fmt"] = fmt


def _get_db(ctx) -> RoamDB:
    return RoamDB(ctx.obj["db_path"], ctx.obj["roam_dir"])


@cli.command()
@click.argument("node_id")
@click.pass_context
def get(ctx, node_id):
    """Resolve a node ID to its file path and metadata."""
    with _get_db(ctx) as db:
        node = db.get_node(node_id)
        if not node:
            click.echo(json.dumps({"error": f"Node {node_id} not found"}), err=True)
            sys.exit(1)
        _output(node.model_dump(), ctx.obj["fmt"])


@cli.command()
@click.argument("node_id")
@click.pass_context
def backlinks(ctx, node_id):
    """List all nodes that link to the given ID."""
    with _get_db(ctx) as db:
        links = db.get_backlinks(node_id)
        _output([l.model_dump() for l in links], ctx.obj["fmt"])


@cli.command()
@click.argument("node_id")
@click.pass_context
def links(ctx, node_id):
    """List all nodes that the given ID links to (forward links)."""
    with _get_db(ctx) as db:
        fwd_links = db.get_forward_links(node_id)
        _output([l.model_dump() for l in fwd_links], ctx.obj["fmt"])


@cli.command()
@click.option("--id", "node_id", default=None, help="Center node ID")
@click.option("--depth", default=2, help="Traversal depth")
@click.pass_context
def graph(ctx, node_id, depth):
    """Return a subgraph (adjacency list) around a node or the full workspace graph."""
    with _get_db(ctx) as db:
        g = db.get_graph(node_id, depth, ctx.obj["workspace"])
        _output(g, ctx.obj["fmt"])


@cli.command()
@click.argument("query")
@click.option("--tags", default=None, help="Comma-separated tag filter")
@click.option("--dir", "dir_prefix", default=None, help="Directory prefix filter (relative to roam root)")
@click.option("--threshold", default=40, help="Minimum fuzzy match score (0-100)")
@click.option("--limit", default=20, help="Maximum number of results")
@click.pass_context
def search(ctx, query, tags, dir_prefix, threshold, limit):
    """Fuzzy search over titles and aliases."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    with _get_db(ctx) as db:
        nodes = db.search_nodes(
            workspace=ctx.obj["workspace"],
            tags=tag_list,
            dir_prefix=dir_prefix,
        )
        results = fuzzy_search(query, nodes, threshold=threshold, limit=limit)
        _output(
            [{"score": r.score, **r.node.model_dump()} for r in results],
            ctx.obj["fmt"],
        )


@cli.command()
@click.pass_context
def tags(ctx):
    """List all tags in scope."""
    with _get_db(ctx) as db:
        tag_list = db.list_tags(ctx.obj["workspace"])
        _output(tag_list, ctx.obj["fmt"])


@cli.command()
@click.option("--db-path", default=None, help="Set database path")
@click.option("--roam-dir", default=None, help="Set org-roam root directory")
def config(db_path, roam_dir):
    """Configure roam-cli settings."""
    if db_path or roam_dir:
        from .config import load_config

        cfg = load_config()
        if db_path:
            cfg["db_path"] = db_path
        if roam_dir:
            cfg["roam_dir"] = roam_dir
        save_config(cfg)
        click.echo(json.dumps(cfg, indent=2))
    else:
        cfg = interactive_config()
        click.echo("Configuration saved:")
        click.echo(json.dumps(cfg, indent=2))
