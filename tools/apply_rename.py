#!/usr/bin/env python3
"""Apply the COSMAC rename manifest — REP-05 (dry run) and REP-06 (apply).

Usage:
    python tools/apply_rename.py --dry-run     # print per-file change counts
    python tools/apply_rename.py --apply       # move paths and rewrite content

The manifest lives in tools/rename_manifest.yaml. Ordering of `replacements`
is significant and is preserved: longest / most specific patterns run first
so a short pattern cannot corrupt a longer match that contains it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "rename_manifest.yaml"


def load_manifest() -> dict:
    with MANIFEST.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [ROOT / line for line in out.splitlines() if line]


def is_excluded(path: Path, manifest: dict) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    for pattern in manifest["exclude_paths"]:
        pattern = pattern.rstrip("/")
        if rel == pattern or rel.startswith(pattern + "/"):
            return True
    return path.suffix.lower() in manifest["exclude_extensions"]


def line_is_excluded(line: str, compiled: list[re.Pattern]) -> bool:
    return any(p.search(line) for p in compiled)


def rewrite_text(text: str, manifest: dict, compiled: list[re.Pattern]) -> tuple[str, int]:
    """Return (new_text, lines_changed). Excluded lines are passed through."""
    changed = 0
    out_lines = []
    for line in text.splitlines(keepends=True):
        if line_is_excluded(line, compiled):
            out_lines.append(line)
            continue
        new_line = line
        for rule in manifest["replacements"]:
            new_line = new_line.replace(rule["from"], rule["to"])
        if new_line != line:
            changed += 1
        out_lines.append(new_line)
    return "".join(out_lines), changed


def run_paths(manifest: dict, apply: bool) -> None:
    for rename in manifest["path_renames"]:
        src, dst = ROOT / rename["from"], ROOT / rename["to"]
        if not src.exists():
            print(f"  [skip] {rename['from']} (not present)")
            continue
        print(f"  [move] {rename['from']} -> {rename['to']}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "mv", rename["from"], rename["to"]], cwd=ROOT, check=True)

    for target in manifest["path_deletes"]:
        path = ROOT / target
        if not path.exists():
            print(f"  [skip] {target} (not present)")
            continue
        print(f"  [del ] {target}")
        if apply:
            subprocess.run(["git", "rm", "-r", "-q", "-f", target], cwd=ROOT, check=True)


def _replace_occurrences(text: str, old: str, new: str, which) -> tuple[str, int]:
    """Replace selected 1-based occurrences of ``old``. ``which`` is 'all' or a list."""
    if which == "all":
        return text.replace(old, new), text.count(old)

    wanted = set(which)
    out: list[str] = []
    index = 0
    position = 0
    replaced = 0
    while True:
        found = text.find(old, position)
        if found == -1:
            out.append(text[position:])
            break
        index += 1
        out.append(text[position:found])
        if index in wanted:
            out.append(new)
            replaced += 1
        else:
            out.append(old)
        position = found + len(old)
    return "".join(out), replaced


def run_class_renames(manifest: dict, apply: bool) -> None:
    missing: list[str] = []
    # Apply every rule for a file in one pass, so occurrence numbering is
    # computed against the original text rather than against a partly
    # rewritten file.
    by_file: dict[str, list[dict]] = defaultdict(list)
    for rule in manifest["class_renames"]:
        by_file[rule["file"]].append(rule)

    for rel, rules in by_file.items():
        path = ROOT / rel
        if not path.exists():
            print(f"  [skip] {rel} (not present)")
            continue
        original = path.read_text(encoding="utf-8")

        # Build the replacement against the ORIGINAL occurrence order.
        targets: dict[int, str] = {}
        for rule in rules:
            which = rule.get("occurrences", "all")
            if which == "all":
                total = original.count(rule["from"])
                for i in range(1, total + 1):
                    targets[i] = rule["to"]
            else:
                for i in which:
                    targets[i] = rule["to"]

        old = rules[0]["from"]
        total = original.count(old)
        unmapped = [i for i in range(1, total + 1) if i not in targets]
        if unmapped:
            missing.append(f"{rel}: occurrences {unmapped} have no target")

        new_text = original
        for occurrence, target in sorted(targets.items(), reverse=True):
            new_text, _ = _replace_occurrences(new_text, old, target, [occurrence])

        summary = ", ".join(
            f"{i}->{targets[i].replace('Cosmac', '').replace('Middleware', '')}"
            for i in sorted(targets)
        )
        print(f"  [class] {rel}: {total} occurrence(s) [{summary}]")
        if apply and total:
            path.write_text(new_text, encoding="utf-8")

    if missing:
        print("\n  !! UNMAPPED OCCURRENCES — these would fall through to the")
        print("     generic PromptShield -> Cosmac rule and break the API:")
        for line in missing:
            print(f"       {line}")
        raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    apply = bool(args.apply)

    manifest = load_manifest()
    compiled = [re.compile(p) for p in manifest["exclude_line_patterns"]]

    # Class renames run BEFORE the blanket replacements, while the original
    # PromptShieldMiddleware name is still present in all three files.
    print("\n== class renames (three classes shared one name) ==")
    run_class_renames(manifest, apply)

    print("\n== content rewrite ==")
    total_files = total_lines = 0
    for path in tracked_files():
        if not path.exists() or is_excluded(path, manifest):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text, changed = rewrite_text(text, manifest, compiled)
        if changed:
            total_files += 1
            total_lines += changed
            print(f"  {changed:5d}  {path.relative_to(ROOT).as_posix()}")
            if apply:
                path.write_text(new_text, encoding="utf-8")

    print("\n== path moves and deletes ==")
    run_paths(manifest, apply)

    mode = "APPLIED" if apply else "DRY RUN"
    print(f"\n{mode}: {total_lines} lines across {total_files} files")
    if not apply:
        print("Review this output with a second engineer before REP-06.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
