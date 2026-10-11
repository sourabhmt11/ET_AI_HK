"""Tests for the measurement definitions — EVL-02."""

from __future__ import annotations

import pytest

from cosmac.evaluation.metrics import Proportion, wilson_interval


def test_wilson_matches_known_value():
    """EVL-02 acceptance criterion: 7 of 13 gives about 29% to 77%."""
    lo, hi = wilson_interval(7, 13)
    assert 0.28 < lo < 0.30, f"lower bound {lo}"
    assert 0.76 < hi < 0.78, f"upper bound {hi}"


@pytest.mark.parametrize(
    ("successes", "total"),
    [(0, 10), (10, 10), (1, 1), (0, 1), (50, 100), (1, 1000)],
)
def test_wilson_stays_inside_unit_interval(successes, total):
    """The reason for Wilson over the normal approximation."""
    lo, hi = wilson_interval(successes, total)
    assert 0.0 <= lo <= hi <= 1.0


def test_wilson_brackets_the_observed_rate():
    for successes, total in [(3, 10), (7, 13), (99, 100), (1, 100)]:
        lo, hi = wilson_interval(successes, total)
        assert lo <= successes / total <= hi


def test_wilson_narrows_as_sample_grows():
    narrow = wilson_interval(500, 1000)
    wide = wilson_interval(5, 10)
    assert (narrow[1] - narrow[0]) < (wide[1] - wide[0])


def test_empty_denominator_is_no_information():
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_successes_above_total_is_rejected():
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


class TestProportion:
    def test_format_always_carries_interval_and_denominator(self):
        text = Proportion(7, 13).format()
        assert "%" in text
        assert "[" in text and "]" in text
        assert "n=13" in text

    def test_zero_total_is_reported_not_faked(self):
        assert "n/a" in Proportion(0, 0).format()

    def test_observed_rate(self):
        assert Proportion(1, 4).observed == 0.25

    def test_to_dict_round_trip(self):
        data = Proportion(7, 13).to_dict()
        assert data["successes"] == 7
        assert data["total"] == 13
        assert data["ci_lower"] < data["observed"] < data["ci_upper"]
