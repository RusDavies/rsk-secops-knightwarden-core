#!/usr/bin/env python3
"""Validate the core normalized external approval vocabulary document."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "normalized-external-approval-vocabulary.md"
README = ROOT / "README.md"
LEGACY_PRODUCT_SPELLING = "Kight" + "Warden"


class VocabularyError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VocabularyError(message)


def require_tokens(path: Path, tokens: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for token in tokens:
        require(token in content, f"{path.relative_to(ROOT)} missing token: {token}")


def main() -> int:
    require_tokens(DOC, [
        "Normalized workflow record status",
        "Normalized approval decision",
        "Normalized follow-up task state",
        "Normalized evidence sync state",
        "Normalized sync health state",
        "Normalized callback event types",
        "ServiceNow",
        "Jira Service Management",
        "Microsoft approvals",
        "GitHub Issues",
        "Generic webhook/API connector",
        "approved_with_conditions",
        "changes_requested",
        "revoked",
        "unknown",
        "external_workflow_status",
        "external_approval_decision",
        "external_task_state",
        "external_evidence_sync_state",
        "external_workflow_sync_status",
        "external_workflow_event_type",
        "If external workflow sends unknown state/decision",
        "Repository scope note",
        "Integration, connector implementation, and product packaging records",
    ])
    require(LEGACY_PRODUCT_SPELLING not in DOC.read_text(encoding="utf-8"), "legacy product spelling remains")
    require_tokens(README, [
        "docs/normalized-external-approval-vocabulary.md",
        "scripts/check_normalized_external_approval_vocabulary.py",
    ])
    print("normalized_external_approval_vocabulary_ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VocabularyError as exc:
        raise SystemExit(f"validation failed: {exc}")
