---
name: omi
description: CLI for the Omi developer API. Query conversations, memories, action items, and goals; manage dev API keys; ingest transcripts; run semantic search via MCP.
---

# Omi CLI

## Install

```bash
pip install -e .
```

## Credentials

Read in order: `.env.local`, `OMI_API_KEY` environment variable, OS keyring via `omi auth login`. Optional `OMI_MCP_KEY` enables semantic search.

## Commands

All commands accept a global `--json` flag. JSON is compact when stdout is a pipe.

### Check

```bash
omi auth whoami
omi keys list
```

### Conversations

```bash
omi conversations list --limit 25 --since 7d
omi conversations get <id> --transcript
omi conversations create --text "..."
omi conversations create-from-segments --file segments.json
omi conversations update <id> --title "..."
omi conversations delete <id>
```

Segments file shape: `{"transcript_segments": [{text, speaker, speaker_id, is_user, start, end}], "source": "external_integration", "started_at": "...", "finished_at": "...", "language": "en"}`.

### Memories

```bash
omi memories list --categories interesting,manual
omi memories add "..." --category manual --tags a,b
omi memories batch --file memories.json
omi memories update <id> --content "..."
omi memories delete <id>
```

Batch file: JSON array (auto-wrapped) or `{"memories": [...]}`. Up to 25 per call.

### Action items

```bash
omi actions list --pending --conversation <id>
omi actions add "..." --due 2026-04-20T17:00:00Z
omi actions batch --file actions.json
omi actions complete <id>
omi actions delete <id>
```

### Goals

```bash
omi goals list
omi goals add "Run 30 miles" --target 30 --unit miles --due 2026-05-01
omi goals progress <id> --value 12 --note "Week 2"
omi goals history <id>
omi goals delete <id>
```

### Search

```bash
omi search "query"                     # semantic if OMI_MCP_KEY set
omi search "query" --substring         # keyword fallback
omi search "query" --semantic --limit 20
```

### Other

```bash
omi digest --window 7d
omi notes --latest
omi notes --longest --format markdown
omi export --format ndjson --resource all --out dump.ndjson --transcripts
```

## Errors

- 401 / 403 → `omi auth whoami`
- 429 → the CLI retries automatically on rate limits; back off if persistent
- 4xx → printed to stderr as `API error <status>: <detail>`, exit 1
- Input errors (bad date, missing file, malformed JSON) print a single line and exit 2
