from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import click

UTC = timezone.utc

_SUFFIX_RE = re.compile(r"^(\d+)(min|mo|h|d|w|m)$")
_SUFFIX_DELTAS = {
    "min": lambda n: timedelta(minutes=n),
    "h": lambda n: timedelta(hours=n),
    "d": lambda n: timedelta(days=n),
    "w": lambda n: timedelta(weeks=n),
    "mo": lambda n: timedelta(days=n * 30),
    "m": lambda n: timedelta(days=n * 30),
}


def parse_window(value: str | None) -> datetime | None:
    """Parse ISO-8601 or relative shortcuts: today, yesterday, 15min, 2h, 7d, 2w, 3mo."""
    if not value:
        return None
    v = value.strip().lower()
    now = datetime.now(UTC)
    if v == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if v == "yesterday":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    if v in {"week", "this-week"}:
        return now - timedelta(days=now.weekday())
    if v in {"month", "this-month"}:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    m = _SUFFIX_RE.match(v)
    if m:
        return now - _SUFFIX_DELTAS[m.group(2)](int(m.group(1)))

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Unrecognized date: {value!r}") from e


def to_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def window_callback(_ctx, _param, value):
    """Click callback: normalize relative/ISO dates to ISO for the API."""
    if value is None:
        return None
    try:
        return to_iso(parse_window(value))
    except ValueError as e:
        raise click.BadParameter(str(e)) from e
