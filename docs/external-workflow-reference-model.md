# External Workflow Reference Model

## Purpose

KnightWarden needs a portable way to record how a local governance object relates to an external review, approval, task, or evidence workflow.

This model is local-first. It records imported or manually entered references, normalized state, raw external values, authority boundaries, and conflict state. It does not require a live integration or any platform-specific automation.

## Scope

The model covers:

- workflow record identity;
- normalized status, decision, task, evidence sync, and sync health values;
- raw external values preserved for audit;
- authority rules for local evidence versus external human workflow state;
- fail-closed handling for unknown or incomplete external state;
- manual evidence export and attachment references.

It does not define platform clients, live callbacks, credential storage, external record mutation, scheduled synchronization, escalation automation, or organization-specific workflow configuration.

## Reference Object

A workflow reference should be represented as a plain data object with these fields:

```json
{
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
  "sync_error_summary": null
}
```

The schema lives at `schemas/external-workflow-reference.schema.json`.

Fixture examples live in `fixtures/external-workflow-references/` and are validated by `scripts/check_external_workflow_reference_model.py`.

## Required Semantics

- Preserve raw external values alongside normalized values.
- Treat external comments, labels, statuses, and payloads as untrusted input.
- Treat only `approved` and `approved_with_conditions` as positive approval decisions.
- Treat `unknown`, missing, stale, mismatched, or incomplete decision state as non-positive.
- Preserve local evidence freshness and completeness as locally authoritative.
- Record conflicts instead of silently overwriting local state from external workflow state.
- Keep imported references useful without requiring outbound writes or callback processing.

## Normalized Values

Use the values defined in [Normalized External Approval Status and Decision Vocabulary](normalized-external-approval-vocabulary.md):

- `external_workflow_status`
- `external_approval_decision`
- `external_task_state`
- `external_evidence_sync_state`
- `external_workflow_sync_status`
- `external_workflow_event_type`

Unknown external values must map to `unknown` and must not unlock local approval gates.

## Authority Rules

KnightWarden remains authoritative for:

- local governance object identity;
- AI inventory and evidence records;
- evidence freshness;
- local policy and rule outputs;
- reopen triggers caused by AI-tool, evidence, or policy drift.

An external workflow reference can be authoritative only for fields explicitly listed in `authoritative_fields`, such as human decision state, approver identity, external task state, or external workflow audit refs.

If local evidence state and imported external workflow state disagree, preserve both values and set `external_workflow_sync_status` to `conflict` or `partial`.

## Manual Import

Manual imports should capture:

- external record identifier and URL;
- normalized status and decision values;
- raw status and decision values;
- observed timestamp;
- source artifact reference for redacted exported data;
- the person or tool that recorded the import when available.

Manual import must not infer approval from prose, comments, labels, or ticket closure alone. A configured mapping or explicit normalized decision is required.

## Manual Export

Manual evidence exports should include:

- local object identity;
- redacted evidence summary;
- evidence packet reference or digest;
- recommended external workflow fields;
- normalized state guidance for later import;
- warnings that unknown or unmapped external state remains non-positive.

Exports must avoid embedding raw prompts, transcripts, secrets, tokens, mailbox contents, arbitrary uploaded files, or private content unless separately minimized and approved by the caller's own process.

## Validation Requirements

A local validator should reject or flag:

- missing external record identity;
- unknown normalized values not represented as `unknown`;
- positive approval decisions without a clear normalized decision;
- missing raw value preservation for imported state;
- conflicting authoritative fields without conflict status;
- evidence sync marked `verified` without an evidence reference;
- stale local evidence paired with a positive external decision without review status.

The current schema enforces portable shape, allowed normalized values, raw value preservation fields, unique authoritative fields, and closed object structure. Higher-order policy checks can layer on top of this schema as the core rule surface grows.

## Non-Goals

This model does not provide:

- live connector execution;
- credential or secret handling;
- webhook endpoints;
- external record creation or mutation;
- scheduled reconciliation;
- retry/dead-letter processing;
- escalation or reminder automation;
- specialized retention workflow.

Those are deployment and operations concerns outside this core reference model.
