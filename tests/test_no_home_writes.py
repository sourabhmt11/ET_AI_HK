"""The test suite must not write to the developer's real home directory.

REP-04. Spec section 5.7 listed this as "inferred, not confirmed"; it was
confirmed during phase 0 — see docs/cosmac/evidence/rep04_home_writes.txt,
where ~/.cosmac/vault/chroma.sqlite3 and the scan-history database were
written while the baseline suite was running.

Two layers guard it:

* ``tests/conftest.py`` redirects the data directory to a temporary path for
  the whole session, so no test has to remember to do it.
* The tests here fail if that redirection stops working.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _home_data_dirs() -> list[Path]:
    home = Path.home()
    return [home / ".cosmac", home / ".cache" / "cosmac"]


def test_data_dir_env_points_outside_home():
    """conftest must have redirected the data directory away from $HOME."""
    value = os.environ.get("COSMAC_DATA_DIR")
    assert value, (
        "COSMAC_DATA_DIR is not set. tests/conftest.py should redirect the "
        "data directory for the whole session so no test writes to $HOME."
    )
    resolved = Path(value).resolve()
    home = Path.home().resolve()
    assert home not in resolved.parents and resolved != home, (
        f"COSMAC_DATA_DIR={resolved} is inside the real home directory {home}"
    )


def test_engine_default_data_dir_is_redirected():
    """An engine built with no explicit data_dir must not land in $HOME."""
    from cosmac.engine import CosmacEngine

    engine = CosmacEngine()
    data_dir = Path(getattr(engine, "data_dir", "")).resolve()
    home = Path.home().resolve()
    assert home not in data_dir.parents, (
        f"engine data_dir={data_dir} is inside the real home directory {home}"
    )


@pytest.mark.parametrize("path", _home_data_dirs(), ids=lambda p: p.name)
def test_suite_creates_no_home_data_dir(path: Path):
    """A full run must not create or modify COSMAC's directories under $HOME.

    This is the assertion REP-04 asks for. It is deliberately a *presence*
    check rather than an mtime check: a developer may legitimately have run
    the CLI before, and failing on their pre-existing data would be noise.
    What must not happen is the suite creating these afresh on a clean
    machine, which is what CI exercises.
    """
    if path.exists():
        pytest.skip(
            f"{path} already exists on this machine (left by a manual CLI or "
            "API run, not necessarily by the suite). The CI job runs on a "
            "clean checkout where this check is meaningful."
        )
    assert not path.exists()
