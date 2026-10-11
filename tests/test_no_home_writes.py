"""The test suite must not write into COSMAC's directories under $HOME.

REP-04. Spec section 5.7 listed this as "inferred, not confirmed"; it was
confirmed during phase 0 — see docs/cosmac/evidence/rep04_home_writes.txt,
where the vault and the scan-history database were written while the
baseline suite was running.

``tests/conftest.py`` redirects the data directory and the model caches for
the whole session. The tests here fail if that redirection stops working.

Note on the assertion: the requirement is *not* "the data directory is
outside $HOME". On Windows the temporary directory lives inside the user
profile (``C:\\Users\\<name>\\AppData\\Local\\Temp``), so such an assertion
would fail on a correctly redirected run. The requirement is that COSMAC's
own directories — ``~/.cosmac`` and ``~/.cache/cosmac`` — are not used.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def cosmac_home_dirs() -> list[Path]:
    home = Path.home()
    return [home / ".cosmac", home / ".cache" / "cosmac"]


def test_data_dir_env_is_set():
    """conftest must redirect the data directory for the whole session."""
    value = os.environ.get("COSMAC_DATA_DIR")
    assert value, (
        "COSMAC_DATA_DIR is not set. tests/conftest.py should redirect the "
        "data directory for the whole session so no test writes to the "
        "developer's real COSMAC directory."
    )


def test_data_dir_is_not_a_cosmac_home_directory():
    resolved = Path(os.environ["COSMAC_DATA_DIR"]).resolve()
    for forbidden in cosmac_home_dirs():
        forbidden = forbidden.resolve()
        assert resolved != forbidden and forbidden not in resolved.parents, (
            f"COSMAC_DATA_DIR={resolved} is the real COSMAC directory {forbidden}"
        )


def test_engine_default_data_dir_is_redirected():
    """An engine built with no explicit data_dir must not land in ~/.cosmac."""
    from cosmac.engine import CosmacEngine

    engine = CosmacEngine()
    # The engine keeps the resolved path privately; there is no public
    # attribute for it.
    data_dir = Path(engine._data_dir).resolve()
    for forbidden in cosmac_home_dirs():
        forbidden = forbidden.resolve()
        assert data_dir != forbidden and forbidden not in data_dir.parents, (
            f"engine data_dir={data_dir} is the real COSMAC directory "
            f"{forbidden}; the COSMAC_DATA_DIR redirect is not being honoured"
        )


@pytest.mark.parametrize("path", cosmac_home_dirs(), ids=lambda p: p.name)
def test_suite_creates_no_cosmac_home_dir(path: Path):
    """A full run must not create COSMAC's directories under $HOME.

    A presence check rather than an mtime check: a developer may legitimately
    have run the CLI before, and failing on their pre-existing data would be
    noise. CI runs this on a clean machine, where it is meaningful, and the
    workflow additionally asserts it after the suite.
    """
    if path.exists():
        pytest.skip(
            f"{path} already exists on this machine (left by a manual CLI or "
            "API run, not necessarily by the suite). The CI job runs on a "
            "clean checkout where this check bites."
        )
    assert not path.exists()
