#!/usr/bin/env python3
"""Fail if any version string disagrees with the package — REP-09.

``src/cosmac/__init__.py`` is the single source. ``pyproject.toml`` reads it
through ``[tool.hatch.version]``, so it cannot drift. Everything else that
states a version is checked here, because the inherited repository shipped
four different ones at once: package 0.8.1, Docker labels 0.7.5, the MCP
image 0.7.6 and the Helm chart appVersion 0.4.1.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src/cosmac/__init__.py"


def package_version() -> str:
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']',
        SOURCE.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        print(f"REP-09: no __version__ found in {SOURCE}")
        raise SystemExit(1)
    return match.group(1)


#: (file, regex capturing the version, human description)
CHECKS: list[tuple[str, str, str]] = [
    ("Dockerfile", r'(?m)^\s*version="([^"]+)"', "Dockerfile OCI label"),
    (
        "Dockerfile",
        r'org\.opencontainers\.image\.version="([^"]+)"',
        "Dockerfile image version label",
    ),
    ("Dockerfile.mcp", r'(?m)^\s*version="([^"]+)"', "MCP Dockerfile OCI label"),
    (
        "Dockerfile.mcp",
        r'org\.opencontainers\.image\.version="([^"]+)"',
        "MCP image version label",
    ),
    ("deploy/helm/cosmac/Chart.yaml", r'(?m)^appVersion:\s*"?([^"\s]+)"?', "Helm appVersion"),
]


def main() -> int:
    expected = package_version()
    problems: list[str] = []
    checked = 0

    for rel, pattern, description in CHECKS:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for found in re.findall(pattern, text):
            checked += 1
            if found != expected:
                problems.append(f"  {rel}: {description} is {found!r}, expected {expected!r}")

    # pyproject must NOT carry a literal version; it reads the package.
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if re.search(r'(?m)^version\s*=\s*"', pyproject):
        problems.append(
            "  pyproject.toml: has a literal `version = \"...\"`. It should use "
            '`dynamic = ["version"]` with [tool.hatch.version] so the package '
            "stays the single source (REP-09)."
        )

    if problems:
        print(f"REP-09: version drift against {expected!r} from src/cosmac/__init__.py:\n")
        print("\n".join(problems))
        return 1

    print(f"REP-09: {checked} version reference(s) agree with {expected!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
