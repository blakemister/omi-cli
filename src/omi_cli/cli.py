from __future__ import annotations

import json
import sys
from functools import wraps

import click

from omi_cli import __version__
from omi_cli.client import OmiError
from omi_cli.commands import (
    actions,
    auth,
    conversations,
    digest,
    export,
    goals,
    keys,
    memories,
    notes,
    search,
)
from omi_cli.output import stderr


def handle_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except OmiError as e:
            stderr.print(f"[red]API error {e.status}[/red]: {e.detail}")
            sys.exit(1)
        except click.ClickException:
            raise
        except json.JSONDecodeError as e:
            stderr.print(f"[red]Invalid JSON[/red]: {e}")
            sys.exit(2)
        except UnicodeError as e:
            stderr.print(f"[red]Encoding error[/red]: {e}")
            sys.exit(2)
        except RuntimeError as e:
            stderr.print(f"[red]{e}[/red]")
            sys.exit(2)
        except Exception as e:
            stderr.print(f"[red]{type(e).__name__}[/red]: {e}")
            sys.exit(2)

    return wrapper


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="omi")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON instead of tables.")
@click.pass_context
def cli(ctx: click.Context, as_json: bool) -> None:
    """Command-line interface for the Omi AI wearable developer API."""
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json


cli.add_command(auth.group)
cli.add_command(keys.group)
cli.add_command(conversations.group)
cli.add_command(memories.group)
cli.add_command(actions.group)
cli.add_command(goals.group)
cli.add_command(search.command)
cli.add_command(digest.command)
cli.add_command(notes.command)
cli.add_command(export.command)


def _wrap(command: click.Command) -> None:
    if isinstance(command, click.Group):
        for sub in command.commands.values():
            _wrap(sub)
    elif command.callback is not None:
        command.callback = handle_errors(command.callback)


for cmd in cli.commands.values():
    _wrap(cmd)
