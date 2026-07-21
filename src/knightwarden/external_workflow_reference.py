"""Helpers for loading external workflow reference objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knightwarden.schema_validate import SchemaRegistry, SchemaValidationError, validate

JsonObject = dict[str, Any]


class ExternalWorkflowReferenceError(Exception):
    """Raised when an external workflow reference file cannot be loaded."""


def default_schema_registry() -> SchemaRegistry:
    """Return a schema registry rooted at this repository's schema directory."""

    return SchemaRegistry(Path(__file__).resolve().parents[2] / "schemas")


def load_external_workflow_reference(
    path: str | Path,
    *,
    registry: SchemaRegistry | None = None,
    schema_name: str = "external-workflow-reference.schema.json",
) -> JsonObject:
    """Load and schema-validate one external workflow reference JSON file."""

    reference_path = Path(path)
    try:
        with reference_path.open("r", encoding="utf-8") as f:
            instance = json.load(f)
    except FileNotFoundError as exc:
        raise ExternalWorkflowReferenceError(f"external workflow reference not found: {reference_path}") from exc
    except json.JSONDecodeError as exc:
        raise ExternalWorkflowReferenceError(
            f"external workflow reference is not valid JSON: {reference_path}: {exc.msg}"
        ) from exc

    if not isinstance(instance, dict):
        raise ExternalWorkflowReferenceError(
            f"external workflow reference must be a JSON object: {reference_path}"
        )

    schema_registry = registry or default_schema_registry()
    try:
        validate(instance, schema_registry.load(schema_name), schema_registry)
    except SchemaValidationError as exc:
        raise ExternalWorkflowReferenceError(
            f"external workflow reference failed schema validation: {reference_path}: {exc}"
        ) from exc

    return instance
