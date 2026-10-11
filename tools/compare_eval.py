#!/usr/bin/env python3
"""Compare two evaluation runs and render a pull-request comment — EVL-08.

Prints the overall, per-type and benign figures for the head of the branch
and the change from the merge base. Every figure keeps its interval and
denominator, so a 2-point move on 13 samples is visibly not a 2-point move
on 1,300.

The EVL-21 thresholds are printed as *advisory* here. This job does not fail
a build; EVL-21 (M2) makes them blocking on the development regression set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# EVL-21 thresholds, shown but not enforced yet.
DROP_OVERALL = 2.0
DROP_PER_TYPE = 5.0
RISE_BENIGN = 1.0


def load(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def pct(entry: dict | None) -> float | None:
    if not entry or not entry.get("total"):
        return None
    return entry["observed"] * 100.0


def fmt(entry: dict | None) -> str:
    if not entry or not entry.get("total"):
        return "n/a"
    return (
        f"{entry['observed'] * 100:.1f}% "
        f"[{entry['ci_lower'] * 100:.1f}-{entry['ci_upper'] * 100:.1f}%] "
        f"n={entry['total']}"
    )


def delta(head: dict | None, base: dict | None) -> str:
    h, b = pct(head), pct(base)
    if h is None or b is None:
        return "—"
    diff = h - b
    if abs(diff) < 0.05:
        return "±0.0"
    return f"{diff:+.1f}"


def flag(head: dict | None, base: dict | None, limit: float, rising_is_bad: bool) -> str:
    h, b = pct(head), pct(base)
    if h is None or b is None:
        return ""
    diff = (h - b) if rising_is_bad else (b - h)
    return " ⚠️" if diff > limit else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", default="comparison.md")
    args = ap.parse_args()

    head = load(args.head)
    base = load(args.base)
    if head is None:
        Path(args.out).write_text(
            "### Detection regression\n\nThe head evaluation produced no "
            "result file. The run failed; see the job log.\n",
            encoding="utf-8",
        )
        return 0

    h = head["header"]
    lines = [
        "### Detection regression (EVL-08, report only)",
        "",
        f"Sample set `{h['sample_set']}` &middot; {h['sample_count']} samples "
        f"&middot; commit `{h['commit'][:8]}`",
        "",
    ]
    if base is None:
        lines.append("> No merge-base result to compare against; showing this branch only.")
        lines.append("")

    base_overall = (base or {}).get("attack_detection_overall")
    base_benign = (base or {}).get("benign_block_rate")
    head_overall = head["attack_detection_overall"]
    head_benign = head["benign_block_rate"]

    lines += [
        "| Measure | This branch | Δ vs base |",
        "|---|---|---|",
        f"| **Attack detection, overall** | {fmt(head_overall)} | "
        f"{delta(head_overall, base_overall)}"
        f"{flag(head_overall, base_overall, DROP_OVERALL, False)} |",
        f"| **Benign block rate** | {fmt(head_benign)} | "
        f"{delta(head_benign, base_benign)}"
        f"{flag(head_benign, base_benign, RISE_BENIGN, True)} |",
        "",
        "#### By attack type",
        "",
        "| Attack type | This branch | Δ |",
        "|---|---|---|",
    ]
    base_types = (base or {}).get("by_attack_type", {})
    for name, entry in head.get("by_attack_type", {}).items():
        lines.append(
            f"| `{name}` | {fmt(entry)} | {delta(entry, base_types.get(name))}"
            f"{flag(entry, base_types.get(name), DROP_PER_TYPE, False)} |"
        )

    lines += [
        "",
        "<details><summary>Advisory thresholds (blocking from EVL-21)</summary>",
        "",
        f"- overall detection drop > {DROP_OVERALL} points",
        f"- any attack type drop > {DROP_PER_TYPE} points",
        f"- benign block rate rise > {RISE_BENIGN} point",
        "",
        "This job does not fail the build. These become blocking in EVL-21 "
        "(M2) on the development regression set, with a documented override "
        "needing data-scientist and product-owner approval.",
        "",
        "</details>",
        "",
        "> The probe set is a 240-sample internal development set written by "
        "one author. It is not a gate and does not support a D1 claim.",
        "",
    ]

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
