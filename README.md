# KnightWarden Core

Open-core repository for KnightWarden governance primitives.

This repository contains downstream-agnostic core code only: public contracts, local/self-hosted primitives, fictional fixtures, transparent checks, and tests.

## Boundary

- Core package namespace: `knightwarden`.
- Core must not import, depend on, or assume downstream extension packages.
- Core must not depend on management, customer-specific, or portfolio-control repositories.
- Downstream extensions may consume this repository only as an external package or approved release artifact.
- Implementation-specific package names belong in boundary checkers and non-public planning records, not public-facing README prose.

## Current State

This repository contains the Python package scaffold plus the first core nucleus: local schema validation, tenant capacity limiting, tenant admission control, common schema definitions, the normalized external approval vocabulary, the external workflow reference model, and a small external workflow reference loader.

## Core Vocabulary

- `docs/normalized-external-approval-vocabulary.md`
- `scripts/check_normalized_external_approval_vocabulary.py`
- `docs/external-workflow-reference-model.md`
- `schemas/external-workflow-reference.schema.json`
- `src/knightwarden/external_workflow_reference.py`
- `fixtures/external-workflow-references/`
- `scripts/check_external_workflow_reference_model.py`

## Verification

```text
python3 -m compileall -q src scripts tests
python3 scripts/check_core_boundary.py
python3 scripts/check_external_workflow_reference_model.py
python3 scripts/check_normalized_external_approval_vocabulary.py
python3 -m unittest discover -s tests
```
