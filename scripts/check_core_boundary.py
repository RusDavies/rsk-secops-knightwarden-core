#!/usr/bin/env python3
"""Validate the clean core repository boundary."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
}
ALLOWED_PRIVATE_IDENTIFIER_REFERENCES = {"scripts/check_core_boundary.py"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"validation failed: {message}")


def tracked_text_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix in TEXT_SUFFIXES
    ]


def main() -> int:
    require((ROOT / "src" / "knightwarden" / "__init__.py").exists(), "missing core package scaffold")
    for rel in [
        "src/knightwarden/schema_validate.py",
        "src/knightwarden/tenant_capacity_limiter.py",
        "src/knightwarden/tenant_admission_control.py",
        "schemas/common.defs.schema.json",
        "schemas/external-workflow-reference.schema.json",
        "docs/external-workflow-reference-model.md",
        "fixtures/external-workflow-references/manual-in-review.json",
        "fixtures/external-workflow-references/approved-with-conditions.json",
        "fixtures/external-workflow-references/unknown-state-held.json",
        "docs/normalized-external-approval-vocabulary.md",
        "scripts/check_external_workflow_reference_model.py",
        "scripts/check_normalized_external_approval_vocabulary.py",
        "tests/test_core_nucleus.py",
        "tests/test_external_workflow_reference_schema.py",
    ]:
        require((ROOT / rel).exists(), f"missing reviewed core nucleus file: {rel}")
    require(not (ROOT / "src" / "knightwarden_enterprise").exists(), "core must not contain enterprise package")
    require((ROOT / "LICENSE").exists(), "missing Apache-2.0 LICENSE file")
    require(not (ROOT / "docs" / "review").exists(), "internal review records must not remain in the public-facing tree")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for token in [
        "Open-core repository for KnightWarden governance primitives.",
        "first core nucleus",
    ]:
        require(token in readme, f"README.md missing token: {token}")
    require("## Boundary" not in readme, "README.md must not expose a boundary section")
    require("knightwarden_enterprise" not in readme, "README.md must not name private/commercial package identifiers")

    for path in tracked_text_files():
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        if "knightwarden_enterprise" in content:
            require(rel in ALLOWED_PRIVATE_IDENTIFIER_REFERENCES, f"{rel} references knightwarden_enterprise")
        if "from kightwarden." in content or "import kightwarden." in content:
            require(rel in ALLOWED_PRIVATE_IDENTIFIER_REFERENCES, f"{rel} uses legacy kightwarden import path")
        if rel not in ALLOWED_PRIVATE_IDENTIFIER_REFERENCES:
            require("rsk-secops-knightwarden-commercial" not in content, f"{rel} references commercial repo")
            require("rsk-secops-knightwarden-mgmt" not in content, f"{rel} references management repo")
            require("rsk-secops-ai-governance-mgmt" not in content, f"{rel} references management repo")

    print("core_boundary_ok files=%d" % len(tracked_text_files()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
