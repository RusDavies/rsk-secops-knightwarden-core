#!/usr/bin/env python3
"""Validate the core external workflow reference model document."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knightwarden.schema_validate import SchemaRegistry, validate  # noqa: E402

DOC = ROOT / "docs" / "external-workflow-reference-model.md"
FIXTURES = ROOT / "fixtures" / "external-workflow-references"
README = ROOT / "README.md"
SCHEMA = ROOT / "schemas" / "external-workflow-reference.schema.json"

REQUIRED_TOKENS = [
    "External Workflow Reference Model",
    "local-first",
    "Reference Object",
    "Required Semantics",
    "Normalized Values",
    "Authority Rules",
    "Manual Import",
    "Manual Export",
    "Validation Requirements",
    "Non-Goals",
    "external_workflow_status",
    "external_approval_decision",
    "external_task_state",
    "external_evidence_sync_state",
    "external_workflow_sync_status",
    "external_workflow_event_type",
    "Unknown external values must map to `unknown`",
    "Treat only `approved` and `approved_with_conditions` as positive approval decisions.",
    "Record conflicts instead of silently overwriting local state from external workflow state.",
    "[Normalized External Approval Status and Decision Vocabulary](normalized-external-approval-vocabulary.md)",
    "schemas/external-workflow-reference.schema.json",
]

FORBIDDEN_TOKENS = [
    "knightwarden" + "_enterprise",
    "rsk-secops-knightwarden-" + "commercial",
    "rsk-secops-knightwarden-" + "mgmt",
    "paid",
    "commercial",
    "ServiceNow",
    "Jira",
    "Microsoft",
    "GitHub",
    "customer-specific",
    "customer content",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"validation failed: {message}")


def require_tokens(path: Path, tokens: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for token in tokens:
        require(token in content, f"{path.relative_to(ROOT)} missing token: {token}")


def main() -> int:
    content = DOC.read_text(encoding="utf-8")
    require_tokens(DOC, REQUIRED_TOKENS)
    for token in FORBIDDEN_TOKENS:
        require(token not in content, f"core reference model contains downstream token: {token}")
    require_tokens(README, [
        "docs/external-workflow-reference-model.md",
        "schemas/external-workflow-reference.schema.json",
        "scripts/check_external_workflow_reference_model.py",
    ])
    require_tokens(SCHEMA, [
        "External Workflow Reference",
        "external_workflow_status",
        "external_approval_decision",
        "external_task_state",
        "external_evidence_sync_state",
        "external_workflow_sync_status",
        "external_workflow_event_type",
        "additionalProperties",
    ])
    fixture_paths = sorted(FIXTURES.glob("*.json"))
    require(len(fixture_paths) >= 3, "expected at least three external workflow reference fixtures")
    registry = SchemaRegistry(ROOT / "schemas")
    schema = registry.load("external-workflow-reference.schema.json")
    fixture_names = {path.name for path in fixture_paths}
    require(
        {"manual-in-review.json", "approved-with-conditions.json", "unknown-state-held.json"} <= fixture_names,
        "missing expected external workflow reference fixtures",
    )
    for path in fixture_paths:
        instance = json.loads(path.read_text(encoding="utf-8"))
        validate(instance, schema, registry)
    unknown = json.loads((FIXTURES / "unknown-state-held.json").read_text(encoding="utf-8"))
    require(unknown["external_approval_decision"] == "unknown", "unknown-state fixture must remain non-positive")
    require(unknown["raw_decision_value"], "unknown-state fixture must preserve raw decision value")
    print(f"external_workflow_reference_model_ok fixtures={len(fixture_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
