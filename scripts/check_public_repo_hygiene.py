#!/usr/bin/env python3
"""Validate public repository hygiene for generated artifacts."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GITIGNORE_PATTERNS = {
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".venv/",
    "build/",
    "dist/",
    "*.egg-info/",
}
GENERATED_PATH_MARKERS = (
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".venv/",
    "build/",
    "dist/",
    ".egg-info/",
)
GENERATED_SUFFIXES = (".pyc", ".pyo")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"validation failed: {message}")


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in sorted(REQUIRED_GITIGNORE_PATTERNS):
        require(pattern in gitignore, f".gitignore missing generated-artifact pattern: {pattern}")

    tracked_generated = [
        path
        for path in git_ls_files()
        if path.endswith(GENERATED_SUFFIXES) or any(marker in f"{path}/" for marker in GENERATED_PATH_MARKERS)
    ]
    require(not tracked_generated, "generated artifacts are tracked: " + ", ".join(tracked_generated))

    print("public_repo_hygiene_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
