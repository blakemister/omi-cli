from __future__ import annotations

import json


def test_help_lists_all_commands(invoke):
    result = invoke("--help")
    assert result.exit_code == 0
    for cmd in ["auth", "keys", "conversations", "memories", "actions", "search", "digest", "notes", "export"]:
        assert cmd in result.output


def test_keys_list_json(httpx_mock, invoke):
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/keys",
        json=[{"id": "k1", "name": "test", "created_at": "2026-01-01T00:00:00Z"}],
    )
    result = invoke("--json", "keys", "list")
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed[0]["id"] == "k1"


def test_conversations_list_table(httpx_mock, invoke):
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/conversations?limit=25&offset=0",
        json=[
            {
                "id": "c1",
                "created_at": "2026-04-14T00:00:00Z",
                "structured": {"title": "Team sync", "category": "work"},
            }
        ],
    )
    result = invoke("conversations", "list")
    assert result.exit_code == 0
    assert "c1" in result.output
    assert "Team sync" in result.output


def test_search_matches_title_only(httpx_mock, invoke):
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/conversations?limit=100&offset=0",
        json=[
            {"id": "c1", "structured": {"title": "Roadmap review", "overview": ""}, "folder_name": "Work"},
            {"id": "c2", "structured": {"title": "Grocery run", "overview": ""}, "folder_name": "Personal"},
        ],
    )
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/memories?limit=100&offset=0",
        json=[],
    )
    result = invoke("--json", "search", "roadmap", "--substring")
    assert result.exit_code == 0
    hits = json.loads(result.output)
    assert len(hits) == 1
    assert hits[0]["id"] == "c1"


def test_missing_key_errors_cleanly(monkeypatch, tmp_path):
    from click.testing import CliRunner

    from omi_cli.cli import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OMI_API_KEY", raising=False)
    monkeypatch.setattr("omi_cli.config._read_keyring", lambda: None)
    result = CliRunner().invoke(cli, ["keys", "list"])
    assert result.exit_code != 0
    assert "No Omi API key" in result.output
