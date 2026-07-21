from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knightwarden.schema_validate import SchemaRegistry, SchemaValidationError, validate
from knightwarden.tenant_admission_control import SharedTenantAdmissionController, WorkDescriptor
from knightwarden.tenant_capacity_limiter import TenantCapacityBudget, TenantFairQueue


class SchemaValidationTest(unittest.TestCase):
    def test_common_defs_id_accepts_stable_identifiers(self) -> None:
        registry = SchemaRegistry(ROOT / "schemas")
        schema = registry.load("common.defs.schema.json")

        validate("tenant:acme-1", schema["$defs"]["id"], registry, current_schema=schema)

        with self.assertRaises(SchemaValidationError):
            validate("", schema["$defs"]["id"], registry, current_schema=schema)

    def test_registry_loads_refs_from_fallback_schema_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp)
            schema_dir.joinpath("wrapper.schema.json").write_text(
                """{
                  "$schema": "https://json-schema.org/draft/2020-12/schema",
                  "type": "object",
                  "required": ["id"],
                  "properties": {
                    "id": {"$ref": "common.defs.schema.json#/$defs/id"}
                  }
                }""",
                encoding="utf-8",
            )
            registry = SchemaRegistry(schema_dir, fallback_dirs=[ROOT / "schemas"])
            schema = registry.load("wrapper.schema.json")

            validate({"id": "tenant:acme"}, schema, registry)

            with self.assertRaises(SchemaValidationError):
                validate({"id": ""}, schema, registry)


class TenantCapacityLimiterTest(unittest.TestCase):
    def test_queue_limits_and_round_robin_dispatch(self) -> None:
        queue: TenantFairQueue[str] = TenantFairQueue(TenantCapacityBudget(max_queued=2, max_dispatch_per_round=1))

        self.assertTrue(queue.submit("tenant-a", "a1"))
        self.assertTrue(queue.submit("tenant-a", "a2"))
        self.assertFalse(queue.submit("tenant-a", "a3"))
        self.assertTrue(queue.submit("tenant-b", "b1"))

        self.assertEqual(queue.dispatch_round(), [("tenant-a", "a1"), ("tenant-b", "b1")])
        self.assertEqual(queue.dispatch_round(), [("tenant-a", "a2")])


class TenantAdmissionControlTest(unittest.TestCase):
    def test_admission_accepts_then_rejects_when_tenant_queue_is_full(self) -> None:
        controller = SharedTenantAdmissionController(
            default_budget=TenantCapacityBudget(max_queued=1, max_dispatch_per_round=1)
        )

        accepted = controller.admit(WorkDescriptor(tenant_id="tenant-a", work_type="scan", route_name="local"))
        self.assertEqual(accepted.outcome, "accepted")

        controller.queue.submit("tenant-a", WorkDescriptor(tenant_id="tenant-a", work_type="scan", route_name="local"))
        rejected = controller.admit(WorkDescriptor(tenant_id="tenant-a", work_type="scan", route_name="local"))
        self.assertEqual(rejected.outcome, "rejected")
        self.assertEqual(rejected.reason_code, "tenant_capacity_exceeded")


if __name__ == "__main__":
    unittest.main()
