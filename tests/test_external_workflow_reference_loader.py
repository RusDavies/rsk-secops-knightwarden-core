from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from knightwarden.external_workflow_reference import (
    ExternalWorkflowReferenceError,
    load_external_workflow_reference,
)

ROOT = Path(__file__).resolve().parents[1]


class ExternalWorkflowReferenceLoaderTest(unittest.TestCase):
    def test_loads_and_validates_committed_fixture(self) -> None:
        reference = load_external_workflow_reference(
            ROOT / "fixtures" / "external-workflow-references" / "manual-in-review.json"
        )

        self.assertEqual(reference["external_record_id"], "REQ-1001")
        self.assertEqual(reference["external_approval_decision"], "pending")

    def test_rejects_schema_invalid_reference_file(self) -> None:
        fixture = json.loads(
            (ROOT / "fixtures" / "external-workflow-references" / "manual-in-review.json").read_text(
                encoding="utf-8"
            )
        )
        fixture["external_approval_decision"] = "approved-ish"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid-reference.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")

            with self.assertRaisesRegex(ExternalWorkflowReferenceError, "failed schema validation"):
                load_external_workflow_reference(path)

    def test_rejects_non_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "not-json.json"
            path.write_text("{not json", encoding="utf-8")

            with self.assertRaisesRegex(ExternalWorkflowReferenceError, "not valid JSON"):
                load_external_workflow_reference(path)

    def test_rejects_missing_file(self) -> None:
        with self.assertRaisesRegex(ExternalWorkflowReferenceError, "not found"):
            load_external_workflow_reference(ROOT / "fixtures" / "external-workflow-references" / "missing.json")


if __name__ == "__main__":
    unittest.main()
