from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.omi.me"
ENV_KEY = "OMI_API_KEY"
ENV_BASE_URL = "OMI_BASE_URL"
KEYRING_SERVICE = "omi-cli"
KEYRING_USERNAME = "default"


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str

    @property
    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


def load_config(*, require_key: bool = True) -> Config:
    for candidate in (Path.cwd() / ".env.local", Path.cwd() / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)

    key = os.environ.get(ENV_KEY) or _read_keyring()
    base_url = os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/")

    if require_key and not key:
        raise RuntimeError(
            "No Omi API key found. Set OMI_API_KEY in .env.local, export it, "
            "or run `omi auth login`."
        )
    return Config(api_key=key or "", base_url=base_url)


def store_key(key: str) -> None:
    try:
        import keyring

        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
    except Exception as exc:
        raise RuntimeError(f"Failed to store key in OS keyring: {exc}") from exc


def clear_key() -> None:
    try:
        import keyring

        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception:
        pass


def _read_keyring() -> str | None:
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception:
        return None
