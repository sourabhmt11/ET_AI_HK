#!/usr/bin/env python3
"""Fail if the old name appears outside the documented exclusions — REP-07.

Run by CI on every pull request. Exits non-zero and prints every offending
line, so a reintroduced name is visible in the job log rather than only in a
diff.

Three things are allowed to keep the old name, and only these:

1. Paths in the manifest's ``exclude_paths`` — the licence, NOTICE, the
   upstream citation and paper, the changelog history, the COSMAC spec
   (which names the upstream deliberately) and the rename tooling itself.
2. Lines matching ``exclude_line_patterns`` — upstream repository, image and
   package URLs, model and dataset identifiers, and the baseline tag. These
   point at a third party's artefacts; rewriting them would make them wrong.
3. Nothing else.

Note that (2) is not a licence to keep upstream *branding*. REP-08 and
DOC-02 remove the upstream logo, badges and registry defaults. This check
deliberately does not enforce that, because a URL in a NOTICE-style
attribution is legitimate while a logo in the README is not; the two are
separated by story, not by pattern.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "rename_manifest.yaml"

# Every case variant from spec section 9.1.
VARIANTS = re.compile(
    r"prompt[_\- ]shield|promptshield|PROMPT[_\- ]SHIELD|PromptShield|Prompt[_\- ]Shield",
    re.IGNORECASE,
)


def tracked_text_files(manifest: dict) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    excluded = [p.rstrip("/") for p in manifest["exclude_paths"]]
    extensions = set(manifest["exclude_extensions"])

    files = []
    for line in out.splitlines():
        if not line:
            continue
        if any(line == e or line.startswith(e + "/") for e in excluded):
            continue
        path = ROOT / line
        if path.suffix.lower() in extensions or not path.exists():
            continue
        files.append(path)
    return files


def main() -> int:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    allowed = [re.compile(p) for p in manifest["exclude_line_patterns"]]

    offences: list[tuple[str, int, str]] = []
    for path in tracked_text_files(manifest):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not VARIANTS.search(line):
                continue
            if any(p.search(line) for p in allowed):
                continue
            offences.append((path.relative_to(ROOT).as_posix(), lineno, line.strip()[:120]))

    if offences:
        print(f"REP-07: the old name appears in {len(offences)} place(s) outside")
        print("the documented exclusions:\n")
        for rel, lineno, text in offences:
            print(f"  {rel}:{lineno}: {text}")
        print("\nEither rename it, or add a justified exclusion to")
        print("tools/rename_manifest.yaml and say why in the pull request.")
        return 1

    # Spec 9.1 "keep unchanged" — assert the rename did not take these too.
    missing = []
    joined = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in tracked_text_files(manifest)
    )
    for token in manifest.get("must_not_change", []):
        if token not in joined:
            missing.append(token)
    if missing:
        print("REP-07: identifiers that must survive the rename are gone:")
        for token in missing:
            print(f"  {token}")
        return 1

    print("REP-07: clean. No old-name variant outside the documented exclusions,")
    print("and every must-not-change identifier is still present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
