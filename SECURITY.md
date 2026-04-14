# Security

## Reporting

Open a [private security advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) on this repository. Do not file a public issue for credential handling or injection bugs.

## API keys

- `omi auth login` stores the dev key in your OS keyring (Windows Credential Manager, macOS Keychain, Secret Service on Linux).
- `.env.local` is gitignored. Never commit a key.
- The CLI sends the key only as a `Authorization: Bearer` header to `https://api.omi.me`. When `OMI_MCP_KEY` is set, the MCP token is sent the same way to `https://api.omi.me/v1/mcp/sse`. Nothing else.

## Supported versions

Latest minor during the `0.x` phase.
