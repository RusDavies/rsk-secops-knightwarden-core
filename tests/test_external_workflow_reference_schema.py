from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knightwarden.schema_validate import SchemaRegistry, SchemaValidationError, validate


def valid_reference() -> dict[str, object]:
    return {
        "provider": "external-workflow",
        "external_record_type": "review_request",
        "external_record_id": "REQ-123",
        "external_record_url": "https://workflow.example.invalid/request/REQ-123",
        "external_workflow_status": "in_review",
        "external_approval_decision": "pending",
        "external_task_state": "assigned",
        "external_evidence_sync_state": "uploaded",
        "external_workflow_sync_status": "synced",
        "external_workflow_event_type": "record_updated",
        "raw_status_value": "waiting_for_security_review",
        "raw_decision_value": "not_decided",
        "raw_payload_ref": "artifact://workflow/REQ-123/redacted.json",
        "authoritative_fields": ["decision", "approver", "task_state"],
        "last_observed_at": "2026-07-20T03:45:00Z",
        "sync_error_summary": None,
    }


class ExternalWorkflowReferenceSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SchemaRegistry(ROOT / "schemas")
        self.schema = self.registry.load("external-workflow-reference.schema.json")

    def assert_valid(self, instance: dict[str, object]) -> None:
        validate(instance, self.schema, self.registry)

    def assert_invalid(self, instance: dict[str, object]) -> None:
        with self.assertRaises(SchemaValidationError):
            validate(instance, self.schema, self.registry)

    def test_accepts_portable_manual_reference(self) -> None:
        self.assert_valid(valid_reference())

    def test_rejects_unknown_normalized_value_spelled_as_raw_custom_state(self) -> None:
        reference = valid_reference()
        reference["external_approval_decision"] = "approved-ish"

        self.assert_invalid(reference)

    def test_accepts_unknown_when_external_value_is_preserved_as_raw(self) -> None:
        reference = valid_reference()
        reference["external_approval_decision"] = "unknown"
        reference["raw_decision_value"] = "approved-ish"
        reference["external_workflow_sync_status"] = "partial"

        self.assert_valid(reference)

    def test_rejects_missing_record_identity(self) -> None:
        reference = valid_reference()
        del reference["external_record_id"]

        self.assert_invalid(reference)

    def test_rejects_extra_live_connector_fields(self) -> None:
        reference = valid_reference()
        reference["credential_ref"] = "secret-ref:not-core"

        self.assert_invalid(reference)

    def test_rejects_duplicate_authoritative_fields(self) -> None:
        reference = valid_reference()
        reference["authoritative_fields"] = ["decision", "decision"]

        self.assert_invalid(reference)

    def test_rejects_unapproved_url_scheme(self) -> None:
        reference = valid_reference()
        reference["external_record_url"] = "ftp://workflow.example.invalid/request/REQ-123"

        self.assert_invalid(reference)

    def test_positive_approval_can_be_represented_with_raw_value_preserved(self) -> None:
        reference = copy.deepcopy(valid_reference())
        reference["external_workflow_status"] = "approved"
        reference["external_approval_decision"] = "approved"
        reference["external_task_state"] = "completed"
        reference["external_evidence_sync_state"] = "verified"
        reference["external_workflow_event_type"] = "approved"
        reference["raw_decision_value"] = "approved"

        self.assert_valid(reference)

    def test_committed_fixtures_validate_against_schema(self) -> None:
        fixture_dir = ROOT / "fixtures" / "external-workflow-references"
        paths = sorted(fixture_dir.glob("*.json"))
        self.assertGreaterEqual(len(paths), 3)

        for path in paths:
            with self.subTest(path=path.name):
                self.assert_valid(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
