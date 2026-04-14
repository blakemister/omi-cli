from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv

from omi_cli.client import OmiClient
from omi_cli.config import load_config
from omi_cli.dates import parse_window, to_iso
from omi_cli.output import emit, stderr

MCP_SSE_URL = "https://api.omi.me/v1/mcp/sse"
MCP_KEY_ENV = "OMI_MCP_KEY"
MCP_MAX_RETRIES = 3
MCP_BACKOFF_BASE = 1.0


@click.command(name="search")
@click.argument("query")
@click.option("--since", help="ISO date or shortcut (today, yesterday, 7d, 2w).")
@click.option("--until", help="ISO date or shortcut.")
@click.option("--limit", type=int, default=10, help="Max results to return.")
@click.option("--memories/--no-memories", default=True, help="Also search memories.")
@click.option(
    "--semantic/--substring",
    default=None,
    help="Force semantic (via MCP, needs OMI_MCP_KEY) or substring. "
    "Defaults to semantic when OMI_MCP_KEY is set.",
)
@click.pass_context
def command(ctx, query, since, until, limit, memories, semantic):
    """Semantic search (via MCP) when an MCP key is available; substring fallback."""
    for candidate in (Path.cwd() / ".env.local", Path.cwd() / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
    mcp_key = os.environ.get(MCP_KEY_ENV)
    use_semantic = semantic if semantic is not None else bool(mcp_key)
    if use_semantic and not mcp_key:
        raise click.UsageError(
            f"--semantic requested but {MCP_KEY_ENV} not set. "
            f"Generate an MCP key at https://app.omi.me/settings?section=developer#mcp"
        )
    if use_semantic:
        results = _semantic(mcp_key, query, since, until, limit, memories)
    else:
        results = _substring(query, since, until, limit, memories)
    emit(
        results,
        as_json=ctx.obj["as_json"],
        columns=["kind", "id", "title", "content", "folder", "created_at"],
        title=f"Search ({'semantic' if use_semantic else 'substring'}): {query}",
    )


def _substring(query, since, until, limit, memories):
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    start = to_iso(parse_window(since))
    end = to_iso(parse_window(until))
    results: list[dict] = []
    with OmiClient(load_config()) as c:
        for conv in c.paginate(
            "/v1/dev/user/conversations",
            max_items=max(limit * 20, 200),
            start_date=start,
            end_date=end,
        ):
            haystack = " ".join(
                [
                    conv.get("structured", {}).get("title", ""),
                    conv.get("structured", {}).get("overview", ""),
                    conv.get("folder_name") or "",
                ]
            )
            if pattern.search(haystack):
                results.append(
                    {
                        "kind": "conversation",
                        "id": conv["id"],
                        "title": conv.get("structured", {}).get("title"),
                        "folder": conv.get("folder_name"),
                        "created_at": conv.get("created_at"),
                    }
                )
                if len(results) >= limit:
                    break
        if memories and len(results) < limit:
            for mem in c.paginate("/v1/dev/user/memories", max_items=max(limit * 20, 200)):
                if pattern.search(mem.get("content", "") or ""):
                    results.append(
                        {
                            "kind": "memory",
                            "id": mem["id"],
                            "content": mem.get("content"),
                            "category": mem.get("category"),
                            "created_at": mem.get("created_at"),
                        }
                    )
                    if len(results) >= limit:
                        break
    return results


def _semantic(mcp_key, query, since, until, limit, memories):
    start_date = _to_date(since)
    end_date = _to_date(until)
    headers = {
        "Authorization": f"Bearer {mcp_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    results: list[dict] = []
    with httpx.Client(timeout=45.0) as c:
        c.post(MCP_SSE_URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "omi-cli", "version": "0"}},
        })
        c.post(MCP_SSE_URL, headers=headers, json={
            "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
        })

        args: dict = {"query": query, "limit": limit}
        if start_date:
            args["start_date"] = start_date
        if end_date:
            args["end_date"] = end_date
        conv_body = _call_tool(c, headers, "search_conversations", args)
        for conv in _json_field(conv_body, "conversations"):
            s = conv.get("structured") or {}
            results.append({
                "kind": "conversation",
                "id": conv.get("id"),
                "title": s.get("title"),
                "folder": conv.get("folder_name"),
                "created_at": conv.get("started_at") or conv.get("created_at"),
            })

        if memories:
            mem_body = _call_tool(c, headers, "search_memories", {"query": query, "limit": limit})
            for mem in _json_field(mem_body, "memories"):
                results.append({
                    "kind": "memory",
                    "id": mem.get("id"),
                    "content": mem.get("content"),
                    "category": mem.get("category"),
                    "created_at": mem.get("created_at"),
                })
    return results


def _call_tool(client, headers, name, arguments):
    attempt = 0
    while True:
        attempt += 1
        r = client.post(MCP_SSE_URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 10, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        if r.status_code == 429 and attempt < MCP_MAX_RETRIES:
            time.sleep(_mcp_retry_delay(r, attempt))
            continue
        if 500 <= r.status_code < 600 and attempt < MCP_MAX_RETRIES:
            time.sleep(MCP_BACKOFF_BASE * 2 ** (attempt - 1))
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"MCP {name} HTTP {r.status_code}: {r.text[:200]}")
        for msg in _parse_sse(r.text):
            if msg.get("id") == 10:
                if "error" in msg:
                    raise RuntimeError(f"MCP {name} error: {msg['error']}")
                content = msg.get("result", {}).get("content") or []
                return content[0].get("text", "") if content else ""
        stderr.print(f"[yellow]MCP {name}: no response[/yellow]")
        return ""


def _mcp_retry_delay(response, attempt):
    header = response.headers.get("Retry-After") or response.headers.get("X-RateLimit-Reset")
    if header:
        try:
            return max(1.0, float(header))
        except ValueError:
            pass
    return MCP_BACKOFF_BASE * 2 ** (attempt - 1)


def _parse_sse(text):
    out = []
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                try:
                    out.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass
    return out


def _json_field(text, key):
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data.get(key, []) if isinstance(data, dict) else []


def _to_date(value):
    dt = parse_window(value)
    return dt.strftime("%Y-%m-%d") if dt else None
