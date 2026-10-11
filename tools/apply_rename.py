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
            subprocess.run(["git", "rm", "-r", "-q", target], cwd=ROOT, check=True)


def run_class_renames(manifest: dict, apply: bool) -> None:
    for rule in manifest["class_renames"]:
        path = ROOT / rule["file"]
        if not path.exists():
            print(f"  [skip] {rule['file']} (not present)")
            continue
        text = path.read_text(encoding="utf-8")
        count = text.count(rule["from"])
        print(f"  [class] {rule['file']}: {rule['from']} -> {rule['to']} ({count} occurrences)")
        if apply and count:
            path.write_text(text.replace(rule["from"], rule["to"]), encoding="utf-8")


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
