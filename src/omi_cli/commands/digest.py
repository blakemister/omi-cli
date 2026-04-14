from __future__ import annotations

from collections import Counter, defaultdict

import click

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.dates import parse_window, to_iso
from omi_cli.output import emit, stdout


@click.command(name="digest")
@click.option("--window", default="7d", help="Time window: today, yesterday, 7d, 2w, 1m, or ISO date.")
@click.option("--limit", type=int, default=500, help="Max conversations to aggregate.")
@click.pass_context
def command(ctx: click.Context, window: str, limit: int) -> None:
    """Aggregate recent activity — counts by folder/category and open action items."""
    start = to_iso(parse_window(window))
    by_folder: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    buckets: dict[str, list[dict]] = defaultdict(list)

    with OmiClient(load_config()) as c:
        convs = list(
            c.paginate(
                "/v1/dev/user/conversations",
                max_items=limit,
                start_date=start,
            )
        )
        for conv in convs:
            folder = conv.get("folder_name") or "Unfiled"
            category = conv.get("structured", {}).get("category") or "uncategorized"
            by_folder[folder] += 1
            by_category[category] += 1
            buckets[folder].append(conv)

        open_actions = list(
            c.paginate(
                "/v1/dev/user/action-items",
                max_items=limit,
                completed="false",
                start_date=start,
            )
        )

    if ctx.obj["as_json"]:
        emit(
            {
                "window": window,
                "conversation_count": len(convs),
                "by_folder": dict(by_folder),
                "by_category": dict(by_category),
                "open_action_items": open_actions,
            },
            as_json=True,
        )
        return

    stdout.rule(f"Digest — {window} — {len(convs)} conversations")
    emit(
        [{"folder": k, "count": v} for k, v in by_folder.most_common()],
        as_json=False,
        title="By folder",
    )
    emit(
        [{"category": k, "count": v} for k, v in by_category.most_common()],
        as_json=False,
        title="By category",
    )
    if open_actions:
        emit(open_actions, as_json=False, title=f"Open action items ({len(open_actions)})")
    else:
        stdout.print("[green]No open action items.[/green]")
