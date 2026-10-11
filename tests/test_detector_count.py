"""The documented detector count must match the registry — DOC-02.

The inherited README stated the detector count in several places and they
disagreed with each other and with the code. The number is now stated once
in the README and asserted here, so documentation cannot drift from the
registry without a test failing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

#: The number of input detectors COSMAC ships. Change this only together
#: with the registry and the README.
EXPECTED_DETECTORS = 35


def registry_count() -> int:
    from cosmac.registry import DetectorRegistry

    registry = DetectorRegistry()
    try:
        registry.discover()
    except AttributeError:
        pass
    detectors = getattr(registry, "detectors", None) or getattr(registry, "_detectors", {})
    return len(detectors)


def test_registry_has_the_expected_number_of_detectors():
    count = registry_count()
    assert count == EXPECTED_DETECTORS, (
        f"the registry holds {count} detectors, not {EXPECTED_DETECTORS}. "
        "Update EXPECTED_DETECTORS and the README together."
    )


def test_detector_ids_are_contiguous():
    """d001..d035 with no gaps, so the README's range is honest."""
    detector_dir = ROOT / "src/cosmac/detectors"
    ids = sorted(
        int(m.group(1))
        for path in detector_dir.glob("d*.py")
        if (m := re.match(r"^d(\d{3})_", path.name))
    )
    assert ids, "no detector modules found"
    assert ids == list(range(1, max(ids) + 1)), f"gaps in detector IDs: {ids}"
    assert max(ids) == EXPECTED_DETECTORS


@pytest.mark.skipif(not README.exists(), reason="README.md absent")
def test_readme_states_the_count_once_and_correctly():
    text = README.read_text(encoding="utf-8")
    # The README states the count in bold, once.
    matches = re.findall(r"\*\*(\d+)\*\* input detectors", text)
    assert matches, "README does not state the input detector count"
    assert len(matches) == 1, f"the count is stated {len(matches)} times; state it once"
    assert int(matches[0]) == EXPECTED_DETECTORS, (
        f"README says {matches[0]} input detectors, registry has {EXPECTED_DETECTORS}"
    )


@pytest.mark.skipif(not README.exists(), reason="README.md absent")
def test_readme_makes_no_metrics_claim():
    """DOC-02: no claim about /metrics that does not hold."""
    text = README.read_text(encoding="utf-8")
    # Mentioning it to say it does NOT exist is required; claiming it does is not.
    bad = re.search(r"Prometheus\s+`?/metrics`?\s+observability", text, re.IGNORECASE)
    assert not bad, (
        "README advertises a /metrics endpoint. api.py serves no such route."
    )
    assert "no `/metrics` route" in text.lower() or "there is no `/metrics`" in text.lower(), (
        "README should state plainly that /metrics is not served"
    )
