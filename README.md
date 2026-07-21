# KnightWarden Core

[![CI](https://github.com/RusDavies/rsk-secops-knightwarden-core/actions/workflows/ci.yml/badge.svg)](https://github.com/RusDavies/rsk-secops-knightwarden-core/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Open-core repository for KnightWarden governance primitives.

This repository contains portable governance primitives: public contracts, local validation helpers, example fixtures, transparent checks, and tests.

## Current State

This repository currently includes local schema validation, tenant capacity limiting, tenant admission control, common schema definitions, the normalized external approval vocabulary, the external workflow reference model, and a small external workflow reference loader.

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

## Contributing and Security

- See `CONTRIBUTING.md` before opening a pull request.
- See `SECURITY.md` for vulnerability reporting.
