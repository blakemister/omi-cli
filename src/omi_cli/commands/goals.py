from __future__ import annotations

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.output import emit

BASE = "/v1/dev/user/goals"


@click.group(name="goals")
def group() -> None:
    """Manage goals (list, create, progress, history)."""


def _client() -> OmiClient:
    return OmiClient(load_config())


@group.command("list")
@click.option("--limit", type=int, default=25)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_cmd(ctx, limit, offset):
    with _client() as c:
        data = c.get(BASE, limit=limit, offset=offset)
    emit(data, as_json=ctx.obj["as_json"], title="Goals")


@group.command("get")
@click.argument("goal_id")
@click.pass_context
def get_cmd(ctx, goal_id):
    with _client() as c:
        data = c.get(f"{BASE}/{goal_id}")
    emit(data, as_json=ctx.obj["as_json"])


@group.command("add")
@click.argument("title")
@click.option("--description")
@click.option("--target", type=float, help="Numeric target value.")
@click.option("--unit", help="Unit (e.g. 'km', 'books', 'hours').")
@click.option("--due", "due_at", help="ISO-8601 due date.")
@click.pass_context
def add_cmd(ctx, title, description, target, unit, due_at):
    body = {
        "title": title,
        "description": description,
        "target": target,
        "unit": unit,
        "due_at": due_at,
    }
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.post(BASE, json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("update")
@click.argument("goal_id")
@click.option("--title")
@click.option("--description")
@click.option("--target", type=float)
@click.option("--unit")
@click.option("--due", "due_at")
@click.pass_context
def update_cmd(ctx, goal_id, title, description, target, unit, due_at):
    body = {
        "title": title,
        "description": description,
        "target": target,
        "unit": unit,
        "due_at": due_at,
    }
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.patch(f"{BASE}/{goal_id}", json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("progress")
@click.argument("goal_id")
@click.option("--value", type=float, required=True, help="New progress value.")
@click.option("--note", help="Optional progress note.")
@click.pass_context
def progress_cmd(ctx, goal_id, value, note):
    body = {"value": value, "note": note}
    body = {k: v for k, v in body.items() if v is not None}
    with _client() as c:
        data = c.patch(f"{BASE}/{goal_id}/progress", json=body)
    emit(data, as_json=ctx.obj["as_json"])


@group.command("history")
@click.argument("goal_id")
@click.pass_context
def history_cmd(ctx, goal_id):
    with _client() as c:
        data = c.get(f"{BASE}/{goal_id}/history")
    emit(data, as_json=ctx.obj["as_json"], title="Goal history")


@group.command("delete")
@click.argument("goal_id")
@click.pass_context
def delete_cmd(ctx, goal_id):
    with _client() as c:
        emit(c.delete(f"{BASE}/{goal_id}"), as_json=ctx.obj["as_json"])
