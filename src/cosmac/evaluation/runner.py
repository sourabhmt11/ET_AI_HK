"""Evaluation runner and reliability report — EVL-02.

One command runs a sample set through the *shipped default configuration*
and writes both a machine-readable result file and a readable report.

Two rules from spec section 10.2 are enforced here rather than left to the
caller:

* The report header records the commit, the configuration hash, the model
  identifiers and the sample-set hash. A figure with no provenance is not a
  result.
* If the ML classifier (``d022``) failed to load, the run **exits non-zero**.
  A silent "not detected" run would otherwise look like a clean sweep.
"""

from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cosmac.evaluation.metrics import Proportion
from cosmac.evaluation.schema import EvalSample, check_independence, load_samples

__all__ = ["EvalResult", "ClassifierUnavailableError", "run_evaluation", "write_report"]

# Length buckets for latency reporting (NFR-3).
LENGTH_BUCKETS: list[tuple[str, int, int]] = [
    ("0-500", 0, 500),
    ("501-2k", 501, 2_000),
    ("2k-10k", 2_001, 10_000),
    ("10k+", 10_001, 10**9),
]


class ClassifierUnavailableError(RuntimeError):
    """The ML classifier did not load, so the run is not a result."""


def _bucket_for(length: int) -> str:
    for name, lo, hi in LENGTH_BUCKETS:
        if lo <= length <= hi:
            return name
    return LENGTH_BUCKETS[-1][0]


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _machine() -> str:
    return (
        f"{platform.system()} {platform.release()} / {platform.machine()} / "
        f"Python {platform.python_version()}"
    )


@dataclass
class EvalResult:
    """Outcome of one evaluation run."""

    header: dict[str, Any]
    attack_overall: Proportion
    benign_block_rate: Proportion
    by_attack_type: dict[str, Proportion]
    by_source: dict[str, Proportion]
    latency_ms: dict[str, dict[str, float]]
    independence: dict[str, Any]
    per_sample: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "header": self.header,
            "attack_detection_overall": self.attack_overall.to_dict(),
            "benign_block_rate": self.benign_block_rate.to_dict(),
            "by_attack_type": {k: v.to_dict() for k, v in self.by_attack_type.items()},
            "by_source": {k: v.to_dict() for k, v in self.by_source.items()},
            "latency_ms": self.latency_ms,
            "independence": self.independence,
            "per_sample": self.per_sample,
        }


def _classifier_loaded(engine: Any) -> bool:
    """True when d022 is enabled in config and actually has a model."""
    detectors = getattr(engine, "_ps_config", {}).get("detectors", {})
    cfg = detectors.get("d022_semantic_classifier", {})
    if not cfg.get("enabled", False):
        return True  # explicitly disabled is a choice, not a silent failure

    for detector in getattr(engine, "detectors", []):
        if getattr(detector, "detector_id", "") == "d022_semantic_classifier":
            # The inherited detector sets _pipeline to None when transformers
            # is missing or the model could not be fetched.
            if hasattr(detector, "_pipeline"):
                return detector._pipeline is not None
            if hasattr(detector, "_available"):
                return bool(detector._available)
            return True
    return False


def run_evaluation(
    sample_path: str | Path,
    engine: Any | None = None,
    *,
    require_classifier: bool = True,
) -> EvalResult:
    """Run ``sample_path`` through the shipped default configuration."""
    sample_path = Path(sample_path)
    samples = load_samples(sample_path)

    if engine is None:
        from cosmac.engine import CosmacEngine

        engine = CosmacEngine()

    if require_classifier and not _classifier_loaded(engine):
        raise ClassifierUnavailableError(
            "d022 semantic classifier is enabled in the configuration but did "
            "not load. A run with the classifier silently absent would report "
            "misses as clean results, so this is not a valid evaluation. "
            "Install the ml extra, or disable d022 explicitly and re-run."
        )

    attack_hits = attack_total = 0
    benign_blocked = benign_total = 0
    type_hits: dict[str, int] = defaultdict(int)
    type_total: dict[str, int] = defaultdict(int)
    source_hits: dict[str, int] = defaultdict(int)
    source_total: dict[str, int] = defaultdict(int)
    latencies: dict[str, list[float]] = defaultdict(list)
    per_sample: list[dict[str, Any]] = []

    for sample in samples:
        started = time.perf_counter()
        report = engine.scan(sample.text, context={"source_type": sample.source_type})
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        latencies[_bucket_for(len(sample.text))].append(elapsed_ms)

        action = getattr(report.action, "value", str(report.action))
        # "Detected" means the scan did not let the input through untouched.
        detected = action != "pass"

        if sample.label == "attack":
            attack_total += 1
            type_total[sample.attack_type or "unclassified"] += 1
            source_total[sample.source_type] += 1
            if detected:
                attack_hits += 1
                type_hits[sample.attack_type or "unclassified"] += 1
                source_hits[sample.source_type] += 1
        else:
            benign_total += 1
            if detected:
                benign_blocked += 1

        per_sample.append(
            {
                "id": sample.id,
                "label": sample.label,
                "attack_type": sample.attack_type,
                "source_type": sample.source_type,
                "action": action,
                "risk_score": getattr(report, "overall_risk_score", None),
                "detectors": [d.detector_id for d in getattr(report, "detections", [])],
                "latency_ms": round(elapsed_ms, 2),
                "correct": detected if sample.label == "attack" else not detected,
            }
        )

    latency_summary = {
        bucket: {
            "n": len(values),
            "p50": round(statistics.median(values), 2),
            "p95": round(
                sorted(values)[min(len(values) - 1, int(len(values) * 0.95))], 2
            ),
        }
        for bucket, values in sorted(latencies.items())
        if values
    }

    independence = check_independence(samples)
    detector_cfg = getattr(engine, "_ps_config", {})

    header = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": _git_commit(),
        "config_hash": _config_hash(detector_cfg),
        "sample_set": sample_path.as_posix(),
        "sample_set_sha256": _file_hash(sample_path),
        "sample_count": len(samples),
        "machine": _machine(),
        "models": {
            "classifier": detector_cfg.get("detectors", {})
            .get("d022_semantic_classifier", {})
            .get("model_name", "n/a"),
            "embedding": detector_cfg.get("vault", {}).get("embedding_model", "n/a"),
        },
        "classifier_loaded": _classifier_loaded(engine),
    }

    return EvalResult(
        header=header,
        attack_overall=Proportion(attack_hits, attack_total),
        benign_block_rate=Proportion(benign_blocked, benign_total),
        by_attack_type={
            k: Proportion(type_hits[k], type_total[k]) for k in sorted(type_total)
        },
        by_source={
            k: Proportion(source_hits[k], source_total[k]) for k in sorted(source_total)
        },
        latency_ms=latency_summary,
        independence={
            "total": independence.total,
            "independent_payloads": independence.independent_payloads,
            "independent_carriers": independence.independent_carriers,
            "shared_payload_groups": len(independence.shared_payload_groups),
            "shared_carrier_groups": len(independence.shared_carrier_groups),
        },
        per_sample=per_sample,
    )


def write_report(result: EvalResult, out_dir: str | Path) -> tuple[Path, Path]:
    """Write ``results.json`` and ``report.md``; return both paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "results.json"
    json_path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=False), encoding="utf-8"
    )

    h = result.header
    lines = [
        "# COSMAC reliability report",
        "",
        "## Provenance",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Generated (UTC) | {h['generated_utc']} |",
        f"| Commit | `{h['commit']}` |",
        f"| Configuration hash | `{h['config_hash'][:16]}…` |",
        f"| Sample set | `{h['sample_set']}` |",
        f"| Sample-set SHA-256 | `{h['sample_set_sha256'][:16]}…` |",
        f"| Samples | {h['sample_count']} |",
        f"| Machine | {h['machine']} |",
        f"| Classifier | `{h['models']['classifier']}` |",
        f"| Embedding model | `{h['models']['embedding']}` |",
        f"| Classifier loaded | {h['classifier_loaded']} |",
        "",
        "## Headline figures",
        "",
        "Every rate is given as observed value, 95% Wilson interval, and "
        "denominator. No figure in this report may be quoted without its interval.",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Attack detection, overall | {result.attack_overall.format()} |",
        f"| Benign block rate | {result.benign_block_rate.format()} |",
        "",
        "## By attack type",
        "",
        "| Attack type | Detection rate |",
        "|---|---|",
    ]
    for name, prop in result.by_attack_type.items():
        lines.append(f"| `{name}` | {prop.format()} |")

    lines += ["", "## By source type", "", "| Source | Detection rate |", "|---|---|"]
    for name, prop in result.by_source.items():
        lines.append(f"| `{name}` | {prop.format()} |")

    lines += [
        "",
        "## In-process latency",
        "",
        f"Measured on: {h['machine']}",
        "",
        "| Length bucket | n | p50 (ms) | p95 (ms) |",
        "|---|---|---|---|",
    ]
    for bucket, stats in result.latency_ms.items():
        lines.append(f"| {bucket} | {stats['n']} | {stats['p50']} | {stats['p95']} |")

    ind = result.independence
    lines += [
        "",
        "## Independence (spec 10.1)",
        "",
        f"- Samples: {ind['total']}",
        f"- Independent payloads: {ind['independent_payloads']}",
        f"- Independent carriers: {ind['independent_carriers']}",
        f"- Payload IDs reused across samples: {ind['shared_payload_groups']}",
        f"- Carrier IDs reused across samples: {ind['shared_carrier_groups']}",
        "",
    ]

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, report_path
