# omi-cli

Command-line interface for the [Omi](https://omi.me) developer API.

Covers conversations, memories, action items, goals, API keys, digest, export, and notes. Uses the hosted MCP endpoint for semantic search when a second key is configured. Rich tables by default, `--json` for scripts and agents.

## Install

```bash
pip install -e .
```

Provides an `omi` command on your `PATH`.

## Authenticate

The dev key is loaded from the first of:

1. `.env.local` in the working directory
2. the `OMI_API_KEY` environment variable
3. the OS keyring (run `omi auth login` once)

Check it:

```bash
omi auth whoami
```

## Commands

```
omi auth login|logout|whoami
omi keys list|create <name>|revoke <id>

omi conversations list [--limit --offset --since --until --transcript]
omi conversations get <id> [--transcript/--no-transcript]
omi conversations create --text "..." [--source --language]
omi conversations create-from-segments --file segments.json
omi conversations update <id> [--title --discarded]
omi conversations delete <id>

omi memories list [--limit --offset --categories]
omi memories add "content" [--category --visibility --tags]
omi memories batch --file memories.json
omi memories update <id> [--content --visibility]
omi memories delete <id>

omi actions list [--completed/--pending --conversation --since --until]
omi actions add "description" [--due --conversation]
omi actions batch --file actions.json
omi actions complete <id>
omi actions update <id> [--description --due --completed/--pending]
omi actions delete <id>

omi goals list|get|add|update|progress|history|delete

omi search "<query>" [--semantic/--substring --limit --since --until --no-memories]
omi digest [--window 7d --limit 500]
omi notes [<id> | --latest | --longest] [--format markdown|json]
omi export [--format json|ndjson --resource all|conversations|memories|actions --out FILE --transcripts]
```

Dates accept ISO-8601 or shortcuts: `today`, `yesterday`, `7d`, `2w`, `3mo`, `15min`.

Add `--json` before the subcommand for machine output:

```bash
omi --json conversations list --limit 5 | jq '.[].structured.title'
```

JSON is compact when stdout is a pipe and indented when it's a TTY.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `OMI_API_KEY` | — | Required. Dev token starting with `omi_dev_`. |
| `OMI_MCP_KEY` | — | Optional. MCP token (`omi_mcp_...`). Enables semantic search. Generate at [app.omi.me/settings](https://app.omi.me/settings) → developer → MCP. |
| `OMI_BASE_URL` | `https://api.omi.me` | Override for staging. |

## Agent use

With both keys in `.env.local`, `omi search "<query>"` routes to the MCP semantic endpoint. Without `OMI_MCP_KEY` it falls back to substring. `--semantic` and `--substring` force either mode.

The CLI covers commands the MCP does not expose: goals, action-items batch, key management, digest, export, and markdown notes. An agent with the CLI available does not need the MCP registered separately.

Pull a week of transcripts in one request:

```bash
omi --json conversations list --since 7d --transcript
```

See [`docs/BENCHMARK.md`](docs/BENCHMARK.md) for the MCP/CLI comparison methodology.

## Limits

Omi applies 100 req/min per key and 10,000 req/day per user. The CLI surfaces the API's rate-limit envelope on HTTP 429 and retries on 429 and 5xx.

## License

MIT. See [`LICENSE`](LICENSE).
