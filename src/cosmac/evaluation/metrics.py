"""Measurement definitions for the reliability report — EVL-02.

Implements spec section 10.1. Every rate COSMAC publishes is a
:class:`Proportion`: an observed value *and* a 95% Wilson score interval, so
a figure can never be quoted without the sample count it rests on.

The Wilson score interval is used rather than the normal approximation
because the counts here are small and the rates are near 0 or 1, where the
normal approximation produces bounds outside [0, 1].
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["Proportion", "wilson_interval"]

# 97.5th percentile of the standard normal — the two-sided 95% z score.
Z_95 = 1.959963984540054


def wilson_interval(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    """Return the Wilson score interval for ``successes`` out of ``total``.

    >>> lo, hi = wilson_interval(7, 13)
    >>> round(lo, 3), round(hi, 3)
    (0.291, 0.766)

    An empty denominator returns ``(0.0, 1.0)`` — no information, rather than
    a divide-by-zero or a false point estimate.
    """
    if total <= 0:
        return (0.0, 1.0)
    if successes < 0 or successes > total:
        raise ValueError(f"successes={successes} outside 0..{total}")

    p = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    centre = (p + z2 / (2 * total)) / denominator
    margin = (z / denominator) * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total))
    return (max(0.0, centre - margin), min(1.0, centre + margin))


@dataclass(frozen=True)
class Proportion:
    """An observed rate with its 95% Wilson interval and its denominator."""

    successes: int
    total: int

    @property
    def observed(self) -> float:
        return self.successes / self.total if self.total else 0.0

    @property
    def interval(self) -> tuple[float, float]:
        return wilson_interval(self.successes, self.total)

    @property
    def lower(self) -> float:
        return self.interval[0]

    @property
    def upper(self) -> float:
        return self.interval[1]

    def format(self, places: int = 1) -> str:
        """Render as ``61.5% [35.5-82.3%] n=13`` — never a bare percentage."""
        if not self.total:
            return "n/a (no samples)"
        lo, hi = self.interval
        return (
            f"{self.observed * 100:.{places}f}% "
            f"[{lo * 100:.{places}f}-{hi * 100:.{places}f}%] "
            f"n={self.total}"
        )

    def to_dict(self) -> dict[str, float | int]:
        lo, hi = self.interval
        return {
            "successes": self.successes,
            "total": self.total,
            "observed": self.observed,
            "ci_lower": lo,
            "ci_upper": hi,
        }

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.format()
