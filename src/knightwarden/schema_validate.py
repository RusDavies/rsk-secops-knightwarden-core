"""Focused local JSON Schema validator for the prototype schema subset.

This is not trying to be a full Draft 2020-12 implementation. It supports the
keywords used by this repository's schemas so fixture gates can run without a
runtime dependency.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

Json = Any


class SchemaValidationError(Exception):
    pass


class SchemaRegistry:
    def __init__(self, schema_dir: Path, fallback_dirs: list[Path] | None = None):
        self.schema_dir = schema_dir
        self.fallback_dirs = fallback_dirs or []
        self._schemas: dict[str, Json] = {}

    def load(self, name: str) -> Json:
        if name not in self._schemas:
            candidates = [self.schema_dir / name, *(schema_dir / name for schema_dir in self.fallback_dirs)]
            path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
            import json

            with path.open("r", encoding="utf-8") as f:
                self._schemas[name] = json.load(f)
        return self._schemas[name]

    def resolve_ref(self, ref: str, current_schema: Json) -> Json:
        if ref.startswith("#"):
            schema = current_schema
            pointer = ref[1:]
        else:
            filename, _, pointer = ref.partition("#")
            schema = self.load(filename)
        if not pointer:
            return schema
        if not pointer.startswith("/"):
            raise SchemaValidationError(f"unsupported $ref pointer {ref!r}")
        target = schema
        for raw_part in pointer.strip("/").split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            target = target[part]
        return target


def type_matches(instance: Json, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(instance, dict)
    if expected_type == "array":
        return isinstance(instance, list)
    if expected_type == "string":
        return isinstance(instance, str)
    if expected_type == "number":
        return (isinstance(instance, int | float) and not isinstance(instance, bool))
    if expected_type == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected_type == "boolean":
        return isinstance(instance, bool)
    if expected_type == "null":
        return instance is None
    raise SchemaValidationError(f"unsupported schema type {expected_type!r}")


def format_path(base: str, part: str | int) -> str:
    if isinstance(part, int):
        return f"{base}[{part}]"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
        return f"{base}.{part}"
    return f"{base}[{part!r}]"


def validate(instance: Json, schema: Json, registry: SchemaRegistry, *, current_schema: Json | None = None, path: str = "$") -> None:
    current_schema = current_schema or schema

    if "$ref" in schema:
        ref = schema["$ref"]
        target = registry.resolve_ref(ref, current_schema)
        ref_root = current_schema if ref.startswith("#") else target
        validate(instance, target, registry, current_schema=ref_root, path=path)
        return

    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaValidationError(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if "type" in schema:
        expected = schema["type"]
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(instance, item) for item in expected_types):
            raise SchemaValidationError(
                f"{path}: type {type(instance).__name__} does not match {expected_types!r}"
            )

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise SchemaValidationError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(properties))
            if extra:
                raise SchemaValidationError(f"{path}: unexpected key {extra[0]!r}")
        for key, subschema in properties.items():
            if key in instance:
                validate(instance[key], subschema, registry, current_schema=current_schema, path=format_path(path, key))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise SchemaValidationError(f"{path}: length {len(instance)} below minItems {schema['minItems']}")
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            import json

            for item in instance:
                marker = json.dumps(item, sort_keys=True, separators=(",", ":"))
                if marker in seen:
                    raise SchemaValidationError(f"{path}: duplicate array item {item!r}")
                seen.add(marker)
        if "items" in schema:
            for index, item in enumerate(instance):
                validate(item, schema["items"], registry, current_schema=current_schema, path=format_path(path, index))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise SchemaValidationError(f"{path}: string shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            raise SchemaValidationError(f"{path}: string {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, int | float) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaValidationError(f"{path}: value {instance!r} below minimum {schema['minimum']!r}")
        if "maximum" in schema and instance > schema["maximum"]:
            raise SchemaValidationError(f"{path}: value {instance!r} above maximum {schema['maximum']!r}")
