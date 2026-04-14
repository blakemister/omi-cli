# Contributing

Community CLI for the [Omi](https://omi.me) developer API. Not affiliated
with BasedHardware.

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Before a PR

```bash
python -m ruff check src tests
python -m pytest tests/
```

CI runs the same commands on Python 3.10–3.12.

## Filing bugs

Include:
- the command that failed
- full output (redact any `omi_dev_...` or `omi_mcp_...` token)
- `omi --version`

## Adding a command

1. New module under `src/omi_cli/commands/`.
2. Export a `click.Command` or `click.Group`.
3. Register it in `src/omi_cli/cli.py`.
4. Add at least one test in `tests/test_commands.py`.

## Security

Do not paste real API keys in issues or PRs. For credential-handling
bugs, open a private advisory (see `SECURITY.md`) rather than a public
issue.
