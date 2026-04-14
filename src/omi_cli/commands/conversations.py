from __future__ import annotations

import json
from pathlib import Path

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.dates import window_callback
from omi_cli.output import emit

BASE = "/v1/dev/user/conversations"


@click.group(name="conversations")
def group() -> None:
    """List, create, inspect, and modify conversations."""


def _client() -> OmiClient:
    return OmiClient(load_config())


@group.command("list")
@click.option("--limit", type=int, default=25)
@click.option("--offset", type=int, default=0)
@click.option("--since", "start_date", callback=window_callback,
              help="ISO date or shortcut (today, 7d, 2w, 3mo).")
@click.option("--until", "end_date", callback=window_callback,
              help="ISO date or shortcut.")
@click.option("--transcript/--no-transcript", "include_transcript", default=False)
@click.pass_context
def list_cmd(ctx, limit, offset, start_date, end_date, include_transcript):
    with _client() as c:
        data = c.get(
            BASE,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            include_transcript=str(include_transcript).lower() if include_transcript else None,
        )
    emit(data, as_json=ctx.obj["as_json"], title="Conversations")


@group.command("get")
@click.argument("conversation_id")
@click.option("--transcript/--no-transcript", "include_transcript", default=True)
@click.pass_context
def get_cmd(ctx, conversation_id, include_transcript):
    with _client() as c:
        data = c.get(
            f"{BASE}/{conversation_id}",
            include_transcript=str(include_transcript).lower(),
        )
    emit(data, as_json=ctx.obj["as_json"])


@group.command("create")
@click.option("--text", required=True, help="Freeform conversation text to ingest.")
@click.option("--source", default="external_integration")
@click.option("--language", default="en")
@click.pass_context
def create_cmd(ctx, text, source, language):
    with _client() as c:
        data = c.post(BASE, json={"text": text, "source": source, "language": language})
    emit(data, as_json=ctx.obj["as_json"])


@group.command("create-from-segments")
@click.option("--file", "path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.pass_context
def create_from_segments(ctx, path: Path):
    """Create a conversation from a JSON file of transcript segments."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise click.FileError(str(path), hint=f"Invalid JSON: {e}") from e
    with _client() as c:
        data = c.post(f"{BASE}/from-segments", json=payload)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("update")
@click.argument("conversation_id")
@click.option("--title")
@click.option("--discarded/--not-discarded", default=None)
@click.pass_context
def update_cmd(ctx, conversation_id, title, discarded):
    body = {k: v for k, v in {"title": title, "discarded": discarded}.items() if v is not None}
    with _client() as c:
        data = c.patch(f"{BASE}/{conversation_id}", json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("delete")
@click.argument("conversation_id")
@click.pass_context
def delete_cmd(ctx, conversation_id):
    with _client() as c:
        emit(c.delete(f"{BASE}/{conversation_id}"), as_json=ctx.obj["as_json"])
