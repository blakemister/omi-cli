from __future__ import annotations

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.output import emit


@click.group(name="keys")
def group() -> None:
    """Manage developer API keys."""


def _client() -> OmiClient:
    return OmiClient(load_config())


@group.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all developer keys on the account."""
    with _client() as c:
        emit(c.get("/v1/dev/keys"), as_json=ctx.obj["as_json"], title="API Keys")


@group.command("create")
@click.argument("name")
@click.pass_context
def create_cmd(ctx: click.Context, name: str) -> None:
    """Create a new developer key. The secret is shown once."""
    with _client() as c:
        emit(c.post("/v1/dev/keys", json={"name": name}), as_json=ctx.obj["as_json"])


@group.command("revoke")
@click.argument("key_id")
@click.pass_context
def revoke_cmd(ctx: click.Context, key_id: str) -> None:
    """Revoke a developer key by id."""
    with _client() as c:
        emit(c.delete(f"/v1/dev/keys/{key_id}"), as_json=ctx.obj["as_json"])
