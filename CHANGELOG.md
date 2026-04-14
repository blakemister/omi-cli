# Changelog

Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [SemVer](https://semver.org/).

## [0.2.0] - 2026-04-14

### Added
- `goals` command group: list, get, add, update, progress, history, delete.
- `actions batch` endpoint.
- `omi search --semantic` routes to the hosted MCP endpoint via SSE when
  `OMI_MCP_KEY` is set. `--substring` keeps the keyword fallback.
- MCP calls retry on 429 and 5xx with backoff.
- `--json` auto-selects compact output when stdout is a pipe.

### Fixed
- `omi notes --latest` no longer crashes on Windows when transcripts contain
  non-cp1252 characters. Stdout is reconfigured to UTF-8 at entry.
- `conversations list --since` and `actions list --since` now accept the
  same relative shortcuts (`today`, `7d`, `3mo`, `15min`) as `search` and
  `digest`.
- `memories batch` and `conversations create-from-segments` raise a
  `click.FileError` on invalid JSON instead of leaking a traceback.
- `memories batch` auto-wraps a bare JSON array into
  `{"memories": [...]}` to match the server contract.
- `memories add --tags ""` no longer sends `[""]` to the API.
- `auth whoami` no longer hits `/v1/dev/keys` (which rejects dev tokens);
  it validates against `/v1/dev/user/memories?limit=1` instead.
- The top-level error handler now catches `json.JSONDecodeError`,
  `UnicodeError`, and any other `Exception` with a clean message.

### Changed
- `dates.py` parses `5min` as five minutes and `5mo` as five months. Bare
  `5m` still resolves to 30 days for backward compatibility.

## [0.1.0] - 2026-04-14

- Initial CLI: auth, keys, conversations, memories, actions, search,
  digest, notes, export. Dual human/JSON output. `httpx` client with
  retry and offset pagination. CI on Python 3.10/3.11/3.12.
