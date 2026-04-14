from __future__ import annotations

import json
from pathlib import Path

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.dates import window_callback
from omi_cli.output import emit

BASE = "/v1/dev/user/action-items"


@click.group(name="actions")
def group() -> None:
    """Manage action items extracted from conversations."""


def _client() -> OmiClient:
    return OmiClient(load_config())


@group.command("list")
@click.option("--limit", type=int, default=100)
@click.option("--offset", type=int, default=0)
@click.option("--completed/--pending", default=None)
@click.option("--conversation", "conversation_id")
@click.option("--since", "start_date", callback=window_callback,
              help="ISO date or shortcut (today, 7d, 2w, 3mo).")
@click.option("--until", "end_date", callback=window_callback,
              help="ISO date or shortcut.")
@click.pass_context
def list_cmd(ctx, limit, offset, completed, conversation_id, start_date, end_date):
    with _client() as c:
        data = c.get(
            BASE,
            limit=limit,
            offset=offset,
            completed=None if completed is None else str(completed).lower(),
            conversation_id=conversation_id,
            start_date=start_date,
            end_date=end_date,
        )
    emit(data, as_json=ctx.obj["as_json"], title="Action Items")


@group.command("add")
@click.argument("description")
@click.option("--due", "due_at", help="ISO-8601 due date.")
@click.option("--conversation", "conversation_id")
@click.pass_context
def add_cmd(ctx, description, due_at, conversation_id):
    body = {
        "description": description,
        "due_at": due_at,
        "conversation_id": conversation_id,
    }
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.post(BASE, json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("batch")
@click.option("--file", "path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.pass_context
def batch_cmd(ctx, path: Path):
    """Bulk-create action items. File may be a JSON array or {"action_items": [...]}."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise click.FileError(str(path), hint=f"Invalid JSON: {e}") from e
    if isinstance(payload, list):
        payload = {"action_items": payload}
    with _client() as c:
        data = c.post(f"{BASE}/batch", json=payload)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("complete")
@click.argument("action_item_id")
@click.pass_context
def complete_cmd(ctx, action_item_id):
    with _client() as c:
        data = c.patch(f"{BASE}/{action_item_id}", json={"completed": True})
    emit(data, as_json=ctx.obj["as_json"])


@group.command("update")
@click.argument("action_item_id")
@click.option("--description")
@click.option("--due", "due_at")
@click.option("--completed/--pending", default=None)
@click.pass_context
def update_cmd(ctx, action_item_id, description, due_at, completed):
    body = {
        "description": description,
        "due_at": due_at,
        "completed": completed,
    }
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.patch(f"{BASE}/{action_item_id}", json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("delete")
@click.argument("action_item_id")
@click.pass_context
def delete_cmd(ctx, action_item_id):
    with _client() as c:
        emit(c.delete(f"{BASE}/{action_item_id}"), as_json=ctx.obj["as_json"])
