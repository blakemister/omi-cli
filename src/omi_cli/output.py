from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping
from typing import Any

from rich.console import Console
from rich.table import Table

stdout = Console()
stderr = Console(stderr=True)


def emit(data: Any, *, as_json: bool, columns: list[str] | None = None, title: str | None = None) -> None:
    if as_json:
        if sys.stdout.isatty():
            json.dump(data, sys.stdout, indent=2, default=str)
        else:
            json.dump(data, sys.stdout, separators=(",", ":"), default=str)
        sys.stdout.write("\n")
        return

    if data is None:
        stdout.print("[dim]ok[/dim]")
        return

    rows = data if isinstance(data, list) else [data] if isinstance(data, Mapping) else None
    if rows is None or not rows:
        stdout.print(data if not isinstance(data, Mapping) else json.dumps(data, indent=2, default=str))
        return

    cols = columns or _infer_columns(rows)
    table = Table(title=title, show_lines=False, header_style="bold cyan")
    for c in cols:
        table.add_column(c, overflow="fold")
    for row in rows:
        table.add_row(*[_cell(row, c) for c in cols])
    stdout.print(table)


def _infer_columns(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    first = next(iter(rows), {})
    preferred = ["id", "name", "title", "content", "description", "category", "created_at", "completed"]
    keys = list(first.keys()) if isinstance(first, Mapping) else []
    ordered = [k for k in preferred if k in keys]
    rest = [k for k in keys if k not in ordered and not k.startswith("_")]
    return (ordered + rest)[:8]


def _cell(row: Any, col: str) -> str:
    if not isinstance(row, Mapping):
        return str(row)
    value = row.get(col)
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)[:80]
    return str(value)
