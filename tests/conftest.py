from __future__ import annotations

import pytest
from click.testing import CliRunner

from omi_cli.cli import cli
from omi_cli.client import OmiClient
from omi_cli.config import Config


@pytest.fixture
def fake_config() -> Config:
    return Config(api_key="omi_dev_testkey", base_url="https://api.omi.me")


@pytest.fixture
def runner(monkeypatch, fake_config: Config) -> CliRunner:
    monkeypatch.setenv("OMI_API_KEY", fake_config.api_key)
    monkeypatch.setenv("OMI_BASE_URL", fake_config.base_url)
    return CliRunner()


@pytest.fixture
def client(fake_config: Config) -> OmiClient:
    return OmiClient(fake_config)


@pytest.fixture
def invoke(runner):
    def _invoke(*args: str, input: str | None = None):
        return runner.invoke(cli, list(args), input=input, catch_exceptions=False)

    return _invoke
