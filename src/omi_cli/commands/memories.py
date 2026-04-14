from __future__ import annotations

import json
from pathlib import Path

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.output import emit

BASE = "/v1/dev/user/memories"


@click.group(name="memories")
def group() -> None:
    """Manage long-term memories."""


def _client() -> OmiClient:
    return OmiClient(load_config())


@group.command("list")
@click.option("--limit", type=int, default=25)
@click.option("--offset", type=int, default=0)
@click.option("--categories", help="Comma-separated category filter.")
@click.pass_context
def list_cmd(ctx, limit, offset, categories):
    with _client() as c:
        data = c.get(BASE, limit=limit, offset=offset, categories=categories)
    emit(data, as_json=ctx.obj["as_json"], title="Memories")


@group.command("add")
@click.argument("content")
@click.option("--category", default="manual")
@click.option("--visibility", type=click.Choice(["public", "private"]), default="private")
@click.option("--tags", help="Comma-separated tags.")
@click.pass_context
def add_cmd(ctx, content, category, visibility, tags):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    body = {
        "content": content,
        "category": category,
        "visibility": visibility,
        "tags": tag_list or None,
    }
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.post(BASE, json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("batch")
@click.option("--file", "path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.pass_context
def batch_cmd(ctx, path: Path):
    """Create up to 25 memories. File may be a JSON array or {"memories": [...]}."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise click.FileError(str(path), hint=f"Invalid JSON: {e}") from e
    if isinstance(payload, list):
        payload = {"memories": payload}
    with _client() as c:
        data = c.post(f"{BASE}/batch", json=payload)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("update")
@click.argument("memory_id")
@click.option("--content")
@click.option("--visibility", type=click.Choice(["public", "private"]))
@click.pass_context
def update_cmd(ctx, memory_id, content, visibility):
    body = {k: v for k, v in {"content": content, "visibility": visibility}.items() if v is not None}
    with _client() as c:
        data = c.patch(f"{BASE}/{memory_id}", json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("delete")
@click.argument("memory_id")
@click.pass_context
def delete_cmd(ctx, memory_id):
    with _client() as c:
        emit(c.delete(f"{BASE}/{memory_id}"), as_json=ctx.obj["as_json"])
