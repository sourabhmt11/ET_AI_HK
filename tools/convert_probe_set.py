#!/usr/bin/env python3
"""Convert the inherited probe set to the EVL-01 schema — EVL-01.

The probe set under docs/cosmac/evidence/detection_probe/probe.jsonl was
written for the spec's current-state assessment. It uses its own `category`
and `style` fields. This script maps those onto the INT section 1 vocabulary
and adds the fields EVL-01 requires (source_type, trust, split, author,
payload_id, carrier_id).

The review (COSMAC_SPEC_REVIEW.md section 4) asked for two relabellings,
both applied here:

1. `short_fragment` is not an attack type. Those rows are benign-by-design
   probes of over-triggering and keep label `benign`.
2. Tool-abuse samples are instructions arriving in retrieved content, not
   user requests, so they carry trust tier `retrieved`, not `user`.

Output: docs/cosmac/evidence/probe_set_v1.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/cosmac/cosmac/evidence/detection_probe/probe.jsonl"
DST = ROOT / "docs/cosmac/evidence/probe_set_v1.jsonl"

# probe `category` -> INT AttackFamily
ATTACK_TYPE = {
    "instruction_override": "instruction_override",
    "role_change": "role_change",
    "secret_extraction": "secret_extraction",
    "tool_abuse": "tool_abuse",
    "credential_theft": "credential_theft",
    "context_poisoning": "context_poisoning",
    "multi_step_jailbreak": "multi_step",
    "encoded_instructions": "encoded_instruction",
    "indirect_injection": "indirect_injection",
}

# probe `style` -> INT SourceType. Styles that name a carrier format win;
# everything else is a plain user message.
SOURCE_BY_STYLE = {
    "obvious_html": "html",
    "hidden_css": "html",
    "paraphrase_web": "html",
    "non_english_web": "html",
    "obvious_email": "email",
    "polite_email": "email",
    "api_response": "json",
    "code_comment": "source_code",
    "markdown": "markdown",
    "ocr": "ocr_text",
    "paraphrase_pdf": "pdf",
    "word_doc": "docx",
    "embedded_doc": "plain_text",
    "tool_result": "plain_text",
}

# probe `category` -> SourceType for benign rows that describe a carrier.
SOURCE_BY_CATEGORY = {
    "code": "source_code",
    "structured_sources": "json",
    "long_document": "plain_text",
}

# Attack families that, by definition, arrive in content rather than from
# the person typing (review section 4).
RETRIEVED_FAMILIES = {"tool_abuse", "indirect_injection", "context_poisoning"}


def convert() -> int:
    raw_lines = SRC.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in raw_lines if line.strip()]
    out: list[dict] = []

    for row in rows:
        category = row.get("category", "")
        style = row.get("style", "")
        label = row["label"]

        attack_type = ATTACK_TYPE.get(category)

        # Relabelling 1: short_fragment probes over-triggering, not an attack.
        if category == "short_fragment":
            label = "benign"
            attack_type = None

        if label == "benign":
            attack_type = None
        elif attack_type is None:
            attack_type = "unclassified"

        source_type = (
            SOURCE_BY_STYLE.get(style) or SOURCE_BY_CATEGORY.get(category) or "user_message"
        )

        # Relabelling 2: content-borne families are retrieved, not user input.
        if attack_type in RETRIEVED_FAMILIES or source_type not in ("user_message",):
            trust = "retrieved" if attack_type in RETRIEVED_FAMILIES else "user"
        else:
            trust = "user"

        record = {
            "id": row["id"],
            "label": label,
            "text": row["text"],
            "source_type": source_type,
            "trust": trust,
            "split": "development",
            "author": "cosmac-team",
            # Each probe row is one distinct wording, so each is its own
            # payload. No carrier reuse is claimed; EVL-06 supersedes this.
            "payload_id": f"probe-{row['id']}",
            "probe_category": category,
            "probe_style": style,
        }
        if attack_type:
            record["attack_type"] = attack_type
        out.append(record)

    DST.parent.mkdir(parents=True, exist_ok=True)
    with DST.open("w", encoding="utf-8", newline="\n") as fh:
        for record in out:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    attacks = sum(1 for r in out if r["label"] == "attack")
    # Report what actually changed, not what the mapping is capable of
    # changing. On the inherited probe set the short_fragment rows are
    # already labelled benign upstream, so relabelling 1 is a no-op
    # safeguard; relabelling 2 does move rows.
    relabelled_short = sum(
        1
        for src, dst in zip(rows, out, strict=True)
        if src["category"] == "short_fragment" and src["label"] != dst["label"]
    )
    retrieved = sum(1 for r in out if r["trust"] == "retrieved")

    print(f"wrote {len(out)} samples to {DST.relative_to(ROOT).as_posix()}")
    print(f"  attack: {attacks}   benign: {len(out) - attacks}")
    print(f"  relabelling 1 (short_fragment -> benign): {relabelled_short} row(s) changed")
    print(f"  relabelling 2 (content-borne -> trust=retrieved): {retrieved} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(convert())
