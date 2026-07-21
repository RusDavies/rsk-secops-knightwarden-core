# Normalized External Approval Status and Decision Vocabulary

## Purpose

KnightWarden needs one internal vocabulary for approval status, decision, task state, and callback events even when the external workflow system is ServiceNow, Jira Service Management, Microsoft approvals, GitHub Issues, or a generic webhook target.

The goal is not to pretend all workflow systems are identical. They are not. Some are elegant. Some are Jira. The goal is to normalize only the workflow-critical semantics needed for AI governance evidence, audit, reopen logic, and reviewer UX.

## Scope

This vocabulary covers:

- external workflow record lifecycle status;
- approval decision outcome;
- follow-up task state;
- evidence attachment/link sync state;
- callback event types;
- sync health state;
- authority and conflict rules.

It deliberately does not normalize every external platform field, custom workflow state, SLA policy, assignment rule, or comment model.

## Core principles

1. Normalize semantics, not vendor table names.
2. Preserve the raw external value alongside the normalized value.
3. Treat external actor comments and callback payloads as untrusted input.
4. Keep KnightWarden authoritative for AI evidence state.
5. Let external platforms be authoritative for configured human workflow state.
6. Record conflicts as sync exceptions instead of silently overwriting.
7. Keep unknown/vendor-custom values explicit.

## Normalized workflow record status

Use `external_workflow_status` for the lifecycle state of the mapped external record.

| Normalized value | Meaning | Typical use |
|---|---|---|
| `draft` | Record is being prepared but not submitted for workflow. | Local draft or external draft state. |
| `submitted` | Record exists and has been submitted but review/approval has not started. | Intake created, waiting routing. |
| `in_review` | Review or approval workflow is active. | Human review in progress. |
| `changes_requested` | Reviewer requires revision before decision. | Return to requester / update evidence. |
| `approved` | External workflow approved the request. | May update local approval state. |
| `approved_with_conditions` | Approved subject to required conditions/tasks. | Create or update mapped follow-up tasks. |
| `rejected` | External workflow rejected the request. | Close, block, or require new request. |
| `cancelled` | Workflow was cancelled before a final approval/rejection decision. | Preserve local evidence; do not treat as rejection. |
| `expired` | Approval/exception/review lapsed by time policy. | Reopen or revoke according to policy. |
| `revoked` | Prior approval/acceptance was explicitly withdrawn. | Reassessment required. |
| `closed` | Workflow is administratively closed. | Terminal if paired with decision or cancellation. |
| `unknown` | External value cannot be safely mapped. | Store raw value and raise sync review. |

### Status guidance

- `approved` and `approved_with_conditions` are decision-bearing states.
- `closed` is not by itself a decision; pair it with a normalized decision when available.
- `cancelled` is neither approved nor rejected.
- `unknown` must not unlock a KnightWarden approval gate.

## Normalized approval decision

Use `external_approval_decision` for the actual decision outcome.

| Normalized value | Meaning |
|---|---|
| `pending` | No final decision yet. |
| `approved` | Approved without additional conditions beyond normal policy. |
| `approved_with_conditions` | Approved only if recorded conditions are met. |
| `rejected` | Rejected/denied. |
| `changes_requested` | Reviewer requested changes instead of final approval/rejection. |
| `deferred` | Decision intentionally postponed or routed to another body. |
| `cancelled` | Workflow cancelled without decision. |
| `expired` | Prior decision or pending request expired. |
| `revoked` | Prior approval/acceptance withdrawn. |
| `unknown` | External decision cannot be safely mapped. |

### Decision guidance

- Local policy gates may treat only `approved` and `approved_with_conditions` as positive decisions.
- `approved_with_conditions` must carry condition summary and mapped task refs where available.
- `changes_requested`, `deferred`, `cancelled`, `expired`, `revoked`, and `unknown` must not be treated as positive approval.
- Store `raw_decision_value` and `raw_decision_payload_ref` for audit.

## Normalized follow-up task state

Use `external_task_state` for mapped ServiceNow/JSM/GitHub/Microsoft/generic tasks created from findings, conditions, or remediations.

| Normalized value | Meaning |
|---|---|
| `not_started` | Task exists but work has not begun. |
| `assigned` | Task has an owner/assignee. |
| `in_progress` | Work is active. |
| `blocked` | Task cannot progress without dependency or decision. |
| `completed` | Work is complete. |
| `completed_with_exception` | Marked complete but with exception/caveat. |
| `rejected` | Assignee/reviewer rejected the task or completion. |
| `cancelled` | Task cancelled. |
| `overdue` | Due date passed while incomplete. |
| `unknown` | External value cannot be safely mapped. |

### Task guidance

- A parent approval with conditions should not become fully locally satisfied until required mapped tasks are `completed` or explicitly accepted as `completed_with_exception` by policy.
- `unknown`, `blocked`, `rejected`, `cancelled`, and `overdue` should trigger local review or escalation.

## Normalized evidence sync state

Use `external_evidence_sync_state` for attachment/link delivery.

| Normalized value | Meaning |
|---|---|
| `not_required` | Template does not require an evidence attachment/link. |
| `pending_upload` | Evidence packet/link has not been sent yet. |
| `uploaded` | Evidence was uploaded or linked. |
| `verified` | External platform confirms attachment/link exists and matches expected metadata/digest where available. |
| `failed` | Upload/link failed. |
| `rejected` | External platform rejected or removed evidence. |
| `stale` | Evidence was delivered but is no longer current. |
| `unknown` | External evidence state cannot be safely mapped. |

## Normalized sync health state

Use `external_workflow_sync_status` for connector health.

| Normalized value | Meaning |
|---|---|
| `not_configured` | No external workflow connector configured. |
| `pending` | Sync queued or waiting retry. |
| `synced` | Last sync succeeded. |
| `partial` | Some fields/tasks/evidence synced, others failed. |
| `failed` | Last sync failed. |
| `conflict` | Local and external authoritative fields disagree. |
| `stale` | External record has not reconciled within policy window. |
| `disabled` | Connector disabled by configuration or policy. |

## Normalized callback event types

Use `external_workflow_event_type` for inbound or reconciled external events.

| Normalized event | Meaning |
|---|---|
| `record_created` | External record created. |
| `record_updated` | External record changed. |
| `approval_requested` | Approval workflow started/requested. |
| `approved` | Approved. |
| `approved_with_conditions` | Approved with explicit conditions. |
| `rejected` | Rejected/denied. |
| `changes_requested` | Reviewer requested revisions. |
| `deferred` | Decision deferred or routed elsewhere. |
| `cancelled` | Workflow cancelled. |
| `expired` | Workflow or approval expired. |
| `revoked` | Prior approval/acceptance revoked. |
| `reassigned` | Assignee/group changed. |
| `task_created` | Mapped task created. |
| `task_updated` | Mapped task changed. |
| `task_completed` | Mapped task completed. |
| `task_blocked` | Mapped task blocked. |
| `task_rejected` | Mapped task rejected. |
| `evidence_uploaded` | Evidence attachment/link uploaded. |
| `evidence_verified` | Evidence verified. |
| `evidence_failed` | Evidence upload/link failed. |
| `comment_added` | Comment/condition added. |
| `sync_conflict` | Reconciliation conflict detected. |
| `unknown` | Event cannot be safely mapped. |

## Platform mapping notes

### ServiceNow

Typical raw sources:

- `state` / `approval` fields on request/change/task/risk/exception records;
- approval records;
- task state;
- business-rule/webhook payloads;
- attachment API responses.

Suggested mapping examples:

| ServiceNow-style raw value | Normalized value |
|---|---|
| `requested`, `approval_requested` | `in_review` / `approval_requested` |
| `approved` | `approved` |
| `approved_with_conditions` or custom conditional approval | `approved_with_conditions` |
| `rejected`, `denied` | `rejected` |
| `cancelled`, `canceled` | `cancelled` |
| `closed_complete` with approved decision | `approved` or `closed` + decision |
| `closed_incomplete` | `cancelled` or `rejected` depending configured mapping |
| custom/blank/unrecognized | `unknown` |

ServiceNow mapping must be customer-configurable because table names, state values, and workflow plugins vary widely.

### Jira Service Management

Typical raw sources:

- issue status category;
- workflow transition name;
- approval status;
- resolution;
- request participant/approver fields;
- linked task status.

Suggested mapping examples:

| JSM-style raw value | Normalized value |
|---|---|
| `Waiting for approval`, `Awaiting approval` | `in_review` / `approval_requested` |
| `Approved` | `approved` |
| `Declined`, `Rejected` | `rejected` |
| `More information required` | `changes_requested` |
| `Done` with approved resolution | `approved` or `closed` + decision |
| `Cancelled` | `cancelled` |
| custom/unrecognized | `unknown` |

### Microsoft approvals / Power Automate / Teams approvals

Typical raw sources:

- approval response outcome;
- responder identity;
- created/completed timestamps;
- adaptive card/action payload;
- Power Automate flow status.

Suggested mapping examples:

| Microsoft-style raw value | Normalized value |
|---|---|
| `Pending` | `pending` or `in_review` |
| `Approve`, `Approved` | `approved` |
| `Reject`, `Rejected` | `rejected` |
| no response before expiry | `expired` |
| flow cancelled/terminated | `cancelled` |
| custom response option | configured mapping or `unknown` |

### GitHub Issues / Projects

Typical raw sources:

- issue state;
- labels;
- comments from configured approvers;
- review checklist status;
- project status field;
- closing reason where available.

Suggested mapping examples:

| GitHub-style raw value | Normalized value |
|---|---|
| open with `approval-requested` label | `in_review` |
| label/comment command `approved` from configured approver | `approved` |
| label/comment command `changes-requested` | `changes_requested` |
| label/comment command `rejected` | `rejected` |
| closed as not planned | `cancelled` or `rejected` by configured mapping |
| closed as completed with approval label | `approved` or `closed` + decision |
| missing approval label/comment | `unknown` or `pending` depending workflow |

GitHub should be treated as a lightweight workflow target, not as a formal GRC system unless the customer deliberately configures it that way.

### Generic webhook/API connector

Generic webhook targets must send explicit normalized values or a configured mapping table.

Minimum accepted fields:

- external record ID;
- event type;
- workflow status or decision;
- actor identity where available;
- timestamp;
- correlation ID / KnightWarden object ID;
- signature or shared-secret verification metadata.

If the webhook payload lacks a configured mapping, use `unknown` and raise sync review. Do not infer approval from vague prose. The comments section is not an oracle; it is where hope goes to be serialized.

## Authority and conflict rules

### KnightWarden authoritative

- AI inventory and compound tool graph;
- evidence objects and generated evidence packets;
- risk-rule output;
- findings and drift logic;
- local governance object canonical JSON;
- reopen triggers caused by AI-tool changes, stale evidence, or policy drift.

### External workflow platform authoritative when configured

- workflow assignment/routing;
- approver identity;
- approval decision;
- task state;
- external comments/conditions summary;
- workflow audit trail.

### Conflict handling

- If KnightWarden says evidence is stale but external approval remains approved, preserve approval but trigger local `evidence_stale` review/reopen logic.
- If external workflow says approved but required local evidence is missing/stale/failed, do not mark local governance object fully approved; record `conflict` or `partial` sync.
- If external workflow sends unknown state/decision, store raw payload and block local positive approval.
- If two external systems are linked to the same object, each reference must declare authoritative fields; otherwise mark conflict.

## Minimal data shape

Future external workflow references should be able to carry:

```json
{
  "provider": "servicenow",
  "external_record_type": "change_request",
  "external_record_id": "CHG0012345",
  "external_record_url": "https://example.service-now.com/change_request.do?sys_id=...",
  "external_workflow_status": "approved_with_conditions",
  "external_approval_decision": "approved_with_conditions",
  "external_task_state": "completed",
  "external_evidence_sync_state": "verified",
  "external_workflow_sync_status": "synced",
  "raw_status_value": "closed_complete",
  "raw_decision_value": "approved_with_conditions",
  "authoritative_fields": ["decision", "approver", "task_state"],
  "last_synced_at": "2026-05-31T23:59:00Z",
  "sync_error_summary": null
}
```

## Repository scope note

This repository includes:

- normalized vocabulary docs;
- schema fields;
- local validators;
- dry-run fixtures;
- connector-neutral mapping semantics;
- static/imported workflow references;
- manual evidence exports.

Live ServiceNow/JSM/Microsoft/GitHub/generic webhook connector implementations,
credentials, webhook endpoints, site-specific mapping configuration UI,
bidirectional sync, reconciliation jobs, escalation/SLA automation, attachment
verification, and custom external workflow table support should live outside
this core repository.

## Related Documents

Integration, connector implementation, and product packaging records
intentionally live outside the core repository. Core keeps the
connector-neutral vocabulary and local validation surface only.
