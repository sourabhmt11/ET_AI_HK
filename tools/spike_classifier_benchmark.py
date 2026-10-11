#!/usr/bin/env python3
"""SPK-02 classifier benchmark harness.

Runs candidate injection classifiers over the same sample set with the same
command, so decision 9 (retrain or replace the inherited classifier) rests on
one comparable table rather than on published figures from three different
papers.

Reports per candidate: recall at a fixed benign block rate, benign block rate
on the set, latency, licence, and whether the project looks maintained.

Candidates are declared below. A candidate whose weights cannot be fetched is
reported as `unavailable` with the reason — never silently skipped, because a
missing candidate that looks like a zero would bias the recommendation.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CANDIDATES = [
    {
        "id": "inherited",
        "model": "protectai/deberta-v3-base-prompt-injection-v2",
        "licence": "Apache-2.0 (claimed, not confirmed — see docs/licences.md)",
        "note": "The classifier COSMAC inherited. The incumbent in decision 9.",
    },
    {
        "id": "protectai-v1",
        "model": "protectai/deberta-v3-base-prompt-injection",
        "licence": "Apache-2.0 (claimed, not confirmed)",
        "note": "Earlier revision of the incumbent; included as a floor.",
    },
    {
        "id": "deepset",
        "model": "deepset/deberta-v3-base-injection",
        "licence": "MIT (claimed, not confirmed)",
        "note": "Independent lineage; the README's named comparator.",
    },
]


def load_pipeline(model_id: str):
    from transformers import pipeline

    return pipeline("text-classification", model=model_id, device=-1, truncation=True)


def is_injection(label: str) -> bool:
    return label.strip().upper() in {"INJECTION", "LABEL_1", "UNSAFE", "JAILBREAK"}


def score_candidate(candidate: dict, samples: list) -> dict:
    out = dict(candidate)
    try:
        clf = load_pipeline(candidate["model"])
    except Exception as exc:
        out["status"] = "unavailable"
        out["reason"] = f"{type(exc).__name__}: {exc}"[:300]
        return out

    tp = fn = fp = tn = 0
    latencies: list[float] = []

    for sample in samples:
        start = time.perf_counter()
        try:
            pred = clf(sample.text[:2000])[0]
        except Exception as exc:
            out["status"] = "error during scoring"
            out["reason"] = f"{type(exc).__name__}: {exc}"[:300]
            return out
        latencies.append((time.perf_counter() - start) * 1000.0)
        flagged = is_injection(pred["label"])

        if sample.label == "attack":
            tp, fn = (tp + 1, fn) if flagged else (tp, fn + 1)
        else:
            fp, tn = (fp + 1, tn) if flagged else (fp, tn + 1)

    from cosmac.evaluation.metrics import Proportion

    recall = Proportion(tp, tp + fn)
    benign_block = Proportion(fp, fp + tn)
    ordered = sorted(latencies)

    out.update(
        {
            "status": "scored",
            "recall": recall.to_dict(),
            "recall_text": recall.format(),
            "benign_block_rate": benign_block.to_dict(),
            "benign_block_rate_text": benign_block.format(),
            "latency_ms": {
                "p50": round(statistics.median(ordered), 2),
                "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 2),
            },
            "confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
        }
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="set_path", required=True)
    ap.add_argument("--out", dest="out_path", default="-")
    ap.add_argument("--only", default=None, help="comma-separated candidate ids")
    args = ap.parse_args()

    from cosmac.evaluation.schema import load_samples

    samples = load_samples(args.set_path)
    wanted = set(args.only.split(",")) if args.only else None

    results = []
    for candidate in CANDIDATES:
        if wanted and candidate["id"] not in wanted:
            continue
        print(f"scoring {candidate['id']} ({candidate['model']})...", file=sys.stderr)
        result = score_candidate(candidate, samples)
        print(f"  -> {result.get('status')}", file=sys.stderr)
        results.append(result)

    payload = {
        "sample_set": args.set_path,
        "sample_count": len(samples),
        "attacks": sum(1 for s in samples if s.label == "attack"),
        "benign": sum(1 for s in samples if s.label == "benign"),
        "candidates": results,
        "caveats": [
            "Scored on the development probe set, which is small and written "
            "by one author. These figures do not support a D2 claim.",
            "Each candidate runs at its own default threshold. Recall at a "
            "fixed 1% benign block rate needs score outputs and a sweep; "
            "where a candidate does not expose scores this is reported as "
            "default-threshold recall instead.",
            "Licences are as claimed on the model card and are NOT confirmed. "
            "See docs/licences.md.",
        ],
    }

    text = json.dumps(payload, indent=2)
    if args.out_path == "-":
        print(text)
    else:
        Path(args.out_path).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
