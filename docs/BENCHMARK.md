# MCP vs CLI benchmark

A comparison of the hosted Omi MCP (`POST /v1/mcp/sse`) against the CLI's two
search modes. Eight queries, run once in each mode against one developer's
personal account (~100 recent conversations). Specific queries and results
are omitted because the corpus is private; only the class of query and the
aggregate numbers are published here.

## Recall and latency

| | MCP SSE | CLI substring |
|---|---|---|
| Queries with ≥1 hit | 8/8 | 1/8 |
| Recall vs MCP | 100% | 2.5% |
| Median latency | 780 ms | 16,650 ms |

The CLI's substring search matched only the one query class where the exact
token appeared in a conversation title. Every other query returned nothing.

## Per-query class

| Query class | MCP hits | CLI hits |
|---|---|---|
| Literal common noun | 10 | 2 |
| Synonym / paraphrase | 10 | 0 |
| Typo | 10 | 0 |
| Conceptual | 10 | 0 |
| Temporal ("what did I decide on \<day\>") | 0 | 0 |
| Abbreviation vs expansion | 10 | 0 |
| Short topical phrase | 10 | 0 |
| Multi-word natural phrase | 10 | 0 |

Both engines miss temporal queries. The MCP has no date-aware parser, and
the CLI's `--since` and `--until` are separate flags.

## Context cost

| | Per session (idle) | On demand |
|---|---|---|
| MCP SSE tools/list | 4,045 B (~1,011 tok) | — |
| MCP stdio tools/list | 5,165 B (~1,291 tok) | — |
| CLI | 0 | `omi --help` ≈ 210 tok per group |

An agent that loads the MCP tool schema pays the token cost whether it
calls any tool or not. `omi --help` loads only when invoked.

## Cold start

| | Median |
|---|---|
| MCP stdio (`python -m mcp_server_omi`) | 1,000 ms |
| MCP SSE (HTTP) | ~70 ms per RPC |
| CLI (`omi --version`) | 275 ms |

## Tool coverage

MCP stdio (7 tools): `get_memories`, `create_memory`, `delete_memory`,
`edit_memory`, `get_conversations`, `get_conversation_by_id`, `create_user`.

MCP SSE (8 tools): the stdio set minus `create_user`, plus `search_memories`
and `search_conversations` (Pinecone-backed).

CLI: auth, keys, conversations, memories (CRUD + batch), actions
(CRUD + batch), goals (CRUD + progress + history), search, digest, notes,
export. The CLI wraps the MCP for semantic search and the dev REST API for
everything else.

## Reproducing

Point the same eight-query pattern at your own account with `OMI_API_KEY`
and `OMI_MCP_KEY` set. The runner under `evals/` is gitignored so real
transcripts never reach the repo.
