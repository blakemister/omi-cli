from __future__ import annotations

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.output import emit, stdout


@click.command(name="notes")
@click.argument("conversation_id", required=False)
@click.option("--latest", is_flag=True, help="Use the most recent conversation.")
@click.option("--longest", is_flag=True, help="Use the longest of the last 25 conversations.")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown")
@click.pass_context
def command(
    ctx: click.Context,
    conversation_id: str | None,
    latest: bool,
    longest: bool,
    fmt: str,
) -> None:
    """Render meeting-notes-style markdown for a conversation."""
    if not conversation_id and not (latest or longest):
        raise click.UsageError("Provide CONVERSATION_ID or --latest / --longest.")

    with OmiClient(load_config()) as c:
        if not conversation_id:
            recent = c.get("/v1/dev/user/conversations", limit=25)
            if not recent:
                raise click.ClickException("No conversations found.")
            if longest:
                def _duration(conv: dict) -> float:
                    from omi_cli.dates import parse_window
                    started = parse_window(conv.get("started_at"))
                    finished = parse_window(conv.get("finished_at"))
                    if not started or not finished:
                        return 0.0
                    return (finished - started).total_seconds()
                pick = max(recent, key=_duration)
            else:
                pick = recent[0]
            conversation_id = pick["id"]

        conv = c.get(f"/v1/dev/user/conversations/{conversation_id}", include_transcript="true")

    if fmt == "json" or ctx.obj["as_json"]:
        emit(conv, as_json=True)
        return

    stdout.print(_to_markdown(conv))


def _to_markdown(conv: dict) -> str:
    s = conv.get("structured", {}) or {}
    lines = [
        f"# {s.get('title') or conv['id']}",
        "",
        f"- **ID**: `{conv['id']}`",
        f"- **When**: {conv.get('started_at')} -> {conv.get('finished_at')}",
        f"- **Folder**: {conv.get('folder_name') or '—'}",
        f"- **Category**: {s.get('category') or '—'}",
        f"- **Language**: {conv.get('language') or '—'}",
    ]
    geo = conv.get("geolocation") or {}
    if geo.get("address"):
        lines.append(f"- **Location**: {geo['address']}")

    overview = s.get("overview")
    if overview:
        lines += ["", "## Overview", "", overview]

    action_items = s.get("action_items") or []
    if action_items:
        lines += ["", "## Action items"]
        for ai in action_items:
            mark = "x" if ai.get("completed") else " "
            due = f" _(due {ai['due_at']})_" if ai.get("due_at") else ""
            lines.append(f"- [{mark}] {ai.get('description', '').strip()}{due}")

    events = s.get("events") or []
    if events:
        lines += ["", "## Events"]
        for e in events:
            lines.append(f"- {e.get('title', '')} — {e.get('start', '')}")

    segments = conv.get("transcript_segments") or []
    if segments:
        lines += ["", "## Transcript"]
        for seg in segments:
            who = seg.get("speaker_name") or f"Speaker {seg.get('speaker_id', '?')}"
            lines.append(f"**{who}**: {seg.get('text', '').strip()}")

    return "\n".join(lines) + "\n"
