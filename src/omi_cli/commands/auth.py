from __future__ import annotations

import click

from omi_cli.client import OmiClient
from omi_cli.config import clear_key, load_config, store_key
from omi_cli.output import emit, stderr, stdout


@click.group(name="auth")
def group() -> None:
    """Manage Omi credentials."""


@group.command("login")
@click.option("--key", prompt="Omi API key (omi_dev_...)", hide_input=True)
def login(key: str) -> None:
    """Store an Omi API key in the OS keyring."""
    if not key.startswith("omi_"):
        stderr.print("[yellow]Warning:[/yellow] key does not start with 'omi_' — storing anyway.")
    store_key(key.strip())
    stdout.print("[green]Stored.[/green] Verify with `omi auth whoami`.")


@group.command("logout")
def logout() -> None:
    """Remove any stored Omi API key from the OS keyring."""
    clear_key()
    stdout.print("[green]Cleared.[/green]")


@group.command("whoami")
@click.pass_context
def whoami(ctx: click.Context) -> None:
    """Verify the current key against a dev-scope endpoint."""
    config = load_config()
    with OmiClient(config) as client:
        client.get("/v1/dev/user/memories", limit=1)
    prefix = (config.api_key[:12] + "...") if config.api_key else "?"
    emit(
        {"authenticated": True, "base_url": config.base_url, "key_prefix": prefix},
        as_json=ctx.obj.get("as_json", False),
    )
