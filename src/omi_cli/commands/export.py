from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.output import stderr


@click.command(name="export")
@click.option("--format", "fmt", type=click.Choice(["json", "ndjson"]), default="ndjson")
@click.option(
    "--resource",
    type=click.Choice(["conversations", "memories", "actions", "all"]),
    default="all",
)
@click.option("--out", "out_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--transcripts/--no-transcripts", default=False, help="Include transcripts for conversations.")
def command(fmt: str, resource: str, out_path: Path | None, transcripts: bool) -> None:
    """Bulk export conversations, memories, and/or action items."""
    endpoints = {
        "conversations": ("/v1/dev/user/conversations", {"include_transcript": "true"} if transcripts else {}),
        "memories": ("/v1/dev/user/memories", {}),
        "actions": ("/v1/dev/user/action-items", {}),
    }
    selected = list(endpoints.keys()) if resource == "all" else [resource]

    sink = out_path.open("w", encoding="utf-8") if out_path else sys.stdout
    try:
        with OmiClient(load_config()) as c:
            if fmt == "json":
                bundle: dict[str, list] = {}
                for name in selected:
                    path, params = endpoints[name]
                    bundle[name] = list(c.paginate(path, **params))
                    stderr.print(f"[dim]{name}: {len(bundle[name])}[/dim]")
                json.dump(bundle, sink, indent=2, default=str)
                sink.write("\n")
            else:
                for name in selected:
                    path, params = endpoints[name]
                    count = 0
                    for item in c.paginate(path, **params):
                        sink.write(json.dumps({"_type": name, **item}, default=str) + "\n")
                        count += 1
                    stderr.print(f"[dim]{name}: {count}[/dim]")
    finally:
        if out_path:
            sink.close()
