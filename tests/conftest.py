"""Shared test fixtures for prompt-shield."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="session", autouse=True)
def _redirect_data_dir_away_from_home() -> Any:
    """Point the data directory at a temporary path for the whole session.

    REP-04. Without this, a test that builds an engine without passing
    ``data_dir`` writes scan history, the vault and downloaded models into
    the developer's real home directory. Spec section 5.7 recorded this as
    inferred; it was confirmed during phase 0 (see
    docs/cosmac/evidence/rep04_home_writes.txt).

    ``autouse`` and session scope are deliberate: making it opt-in is what
    let the leak happen in the first place.
    """
    with tempfile.TemporaryDirectory(prefix="cosmac-tests-") as tmp:
        root = Path(tmp)
        previous = {
            key: os.environ.get(key)
            for key in ("COSMAC_DATA_DIR", "HF_HOME", "SENTENCE_TRANSFORMERS_HOME")
        }
        os.environ["COSMAC_DATA_DIR"] = str(root / "data")
        # Model caches default under $HOME too; keep them out of it as well.
        os.environ["HF_HOME"] = str(root / "models")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(root / "models")
        try:
            yield root
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "prompt_shield_test"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_config(tmp_data_dir: Path) -> dict[str, Any]:
    """Minimal config dict for testing — vault/feedback disabled to avoid heavy deps."""
    return {
        "prompt_shield": {
            "mode": "block",
            "threshold": 0.7,
            "data_dir": str(tmp_data_dir),
            "vault": {"enabled": False},
            "feedback": {"enabled": False},
            "canary": {"enabled": True, "token_length": 16},
            "history": {"enabled": True, "retention_days": 90},
            "threat_feed": {"enabled": False},
            "actions": {
                "critical": "block",
                "high": "block",
                "medium": "flag",
                "low": "log",
            },
            "detectors": {},
            "allowlist": {"patterns": []},
            "blocklist": {"patterns": []},
        }
    }


@pytest.fixture
def engine(sample_config: dict[str, Any], tmp_data_dir: Path):
    """Create a PromptShieldEngine for testing (vault disabled for speed)."""
    from prompt_shield.engine import PromptShieldEngine

    return PromptShieldEngine(config_dict=sample_config, data_dir=str(tmp_data_dir))


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def load_fixture(fixture_path: Path) -> dict[str, Any]:
    """Load a JSON fixture file."""
    return json.loads(fixture_path.read_text(encoding="utf-8"))
