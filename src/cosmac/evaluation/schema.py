"""Evaluation sample schema, loader and independence checker — EVL-01.

Implements spec section 10.1 (definitions) and 10.2 (protocol). The
vocabulary for ``source_type``, ``trust`` and ``attack_type`` is the one in
COSMAC_INTERFACES.md section 1, so a sample set and a scan report describe
the world with the same words.

A sample set is JSON Lines: one :class:`EvalSample` per line.

Independence (spec 10.1) is counted over *payload* and *carrier*: two samples
that reuse the same attack wording, or the same host document, are not two
independent observations. :func:`check_independence` reports those groups so
the evaluation command can state how many independent samples a figure rests
on, rather than quoting a raw row count.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "ATTACK_FAMILIES",
    "SOURCE_TYPES",
    "TRUST_TIERS",
    "EvalSample",
    "IndependenceReport",
    "SchemaError",
    "check_independence",
    "load_samples",
]


class SchemaError(ValueError):
    """A sample set has a missing field or an unknown enumeration value."""


# -- INT section 1 vocabulary -------------------------------------------------

SOURCE_TYPES = frozenset(
    {
        "user_message",
        "html",
        "markdown",
        "email",
        "json",
        "xml",
        "source_code",
        "ocr_text",
        "pdf",
        "docx",
        "image",
        "plain_text",
    }
)

TRUST_TIERS = frozenset(
    {"system", "user", "assistant_history", "tool_description", "retrieved", "memory"}
)

ATTACK_FAMILIES = frozenset(
    {
        "instruction_override",
        "role_change",
        "secret_extraction",
        "tool_abuse",
        "credential_theft",
        "context_poisoning",
        "multi_step",
        "encoded_instruction",
        "indirect_injection",
        "unclassified",
    }
)

LABELS = frozenset({"attack", "benign"})
SPLITS = frozenset({"development", "validation", "test", "sealed"})


@dataclass(frozen=True)
class EvalSample:
    """One evaluation sample.

    ``injected_span`` is ``(start, end)`` in raw offsets of ``text`` when the
    sample is an attack carried inside a benign document; it is ``None`` for a
    direct attack or a benign sample. EVL-07 needs it to compute the
    neutralisation checks.
    """

    id: str
    label: str
    text: str
    source_type: str
    trust: str
    split: str
    author: str
    attack_type: str | None = None
    payload_id: str | None = None
    carrier_id: str | None = None
    injected_span: tuple[int, int] | None = None
    file_ref: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.label not in LABELS:
            raise SchemaError(f"{self.id}: unknown label {self.label!r}")
        if self.source_type not in SOURCE_TYPES:
            raise SchemaError(f"{self.id}: unknown source_type {self.source_type!r}")
        if self.trust not in TRUST_TIERS:
            raise SchemaError(f"{self.id}: unknown trust tier {self.trust!r}")
        if self.split not in SPLITS:
            raise SchemaError(f"{self.id}: unknown split {self.split!r}")
        if self.label == "attack":
            if not self.attack_type:
                raise SchemaError(f"{self.id}: attack sample has no attack_type")
            if self.attack_type not in ATTACK_FAMILIES:
                raise SchemaError(f"{self.id}: unknown attack_type {self.attack_type!r}")
        if self.injected_span is not None:
            start, end = self.injected_span
            if not (0 <= start < end <= len(self.text)):
                raise SchemaError(
                    f"{self.id}: injected_span {self.injected_span} outside text "
                    f"of length {len(self.text)}"
                )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> EvalSample:
        missing = [
            f
            for f in ("id", "label", "text", "source_type", "trust", "split", "author")
            if f not in raw
        ]
        if missing:
            raise SchemaError(f"sample {raw.get('id', '<no id>')}: missing field(s) {missing}")
        span = raw.get("injected_span")
        if span is not None:
            if not (isinstance(span, (list, tuple)) and len(span) == 2):
                raise SchemaError(f"{raw['id']}: injected_span must be [start, end]")
            span = (int(span[0]), int(span[1]))
        known = {
            "id",
            "label",
            "text",
            "source_type",
            "trust",
            "split",
            "author",
            "attack_type",
            "payload_id",
            "carrier_id",
            "injected_span",
            "file_ref",
            "notes",
        }
        return cls(
            id=str(raw["id"]),
            label=raw["label"],
            text=raw["text"],
            source_type=raw["source_type"],
            trust=raw["trust"],
            split=raw["split"],
            author=raw["author"],
            attack_type=raw.get("attack_type"),
            payload_id=raw.get("payload_id"),
            carrier_id=raw.get("carrier_id"),
            injected_span=span,
            file_ref=raw.get("file_ref"),
            notes=raw.get("notes"),
            metadata={k: v for k, v in raw.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "text": self.text,
            "source_type": self.source_type,
            "trust": self.trust,
            "split": self.split,
            "author": self.author,
        }
        for key in ("attack_type", "payload_id", "carrier_id", "file_ref", "notes"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        if self.injected_span is not None:
            out["injected_span"] = list(self.injected_span)
        out.update(self.metadata)
        return out


def load_samples(path: str | Path) -> list[EvalSample]:
    """Load a JSONL sample set, rejecting the whole file on the first bad row."""
    path = Path(path)
    samples: list[EvalSample] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SchemaError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            try:
                sample = EvalSample.from_dict(raw)
            except SchemaError as exc:
                raise SchemaError(f"{path}:{lineno}: {exc}") from exc
            if sample.id in seen:
                raise SchemaError(f"{path}:{lineno}: duplicate sample id {sample.id!r}")
            seen.add(sample.id)
            samples.append(sample)
    if not samples:
        raise SchemaError(f"{path}: no samples")
    return samples


@dataclass
class IndependenceReport:
    """How many of the rows in a set are independent observations."""

    total: int
    independent_payloads: int
    independent_carriers: int
    shared_payload_groups: dict[str, list[str]]
    shared_carrier_groups: dict[str, list[str]]

    @property
    def is_fully_independent(self) -> bool:
        return not self.shared_payload_groups and not self.shared_carrier_groups

    def summary(self) -> str:
        lines = [
            f"samples: {self.total}",
            f"independent payloads: {self.independent_payloads}",
            f"independent carriers: {self.independent_carriers}",
        ]
        if self.shared_payload_groups:
            lines.append(
                f"payload IDs reused by more than one sample: {len(self.shared_payload_groups)}"
            )
        if self.shared_carrier_groups:
            lines.append(
                f"carrier IDs reused by more than one sample: {len(self.shared_carrier_groups)}"
            )
        return "\n".join(lines)


def check_independence(samples: list[EvalSample]) -> IndependenceReport:
    """Report samples that share a payload ID or a carrier ID (spec 10.1)."""
    by_payload: dict[str, list[str]] = defaultdict(list)
    by_carrier: dict[str, list[str]] = defaultdict(list)
    for sample in samples:
        if sample.payload_id:
            by_payload[sample.payload_id].append(sample.id)
        if sample.carrier_id:
            by_carrier[sample.carrier_id].append(sample.id)

    shared_payloads = {k: v for k, v in by_payload.items() if len(v) > 1}
    shared_carriers = {k: v for k, v in by_carrier.items() if len(v) > 1}

    # A sample with no payload_id counts as its own independent payload.
    unlabelled_payloads = sum(1 for s in samples if not s.payload_id)
    unlabelled_carriers = sum(1 for s in samples if not s.carrier_id)

    return IndependenceReport(
        total=len(samples),
        independent_payloads=len(by_payload) + unlabelled_payloads,
        independent_carriers=len(by_carrier) + unlabelled_carriers,
        shared_payload_groups=shared_payloads,
        shared_carrier_groups=shared_carriers,
    )


def count_by(samples: list[EvalSample], attr: str) -> Counter[str]:
    """Count samples by one field, for the coverage matrix (EVL-20)."""
    return Counter(str(getattr(s, attr)) for s in samples)
