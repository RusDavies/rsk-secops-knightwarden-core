"""Shared tenant admission-control interface for processing routes.

This module is route-family agnostic. IDE-agent routes, connector ingest,
webhook ingest, detector/envelope processing, compute jobs, and governed tool
execution should all normalize incoming work into a WorkDescriptor and then use
this layer for tenant fairness/admission decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from knightwarden.tenant_capacity_limiter import TenantCapacityBudget, TenantFairQueue

Json = dict[str, Any]


class AdmissionOutcome(str, Enum):
    """Shared admission outcomes for all processing routes."""

    ACCEPTED = "accepted"
    QUEUED = "queued"
    DEGRADED = "degraded"
    REJECTED = "rejected"
    GLOBAL_OVERLOAD = "global_overload"


@dataclass(frozen=True)
class WorkDescriptor:
    """Normalized description of work before route-specific processing.

    Route-specific request bodies remain route-specific. Admission control only
    consumes this descriptor, so fairness and overload handling can be shared
    across all processing routes.
    """

    tenant_id: str
    work_type: str
    route_name: str
    request_id: str | None = None
    actor_ref: str | None = None
    endpoint_ref: str | None = None
    session_ref: str | None = None
    idempotency_key: str | None = None
    estimated_size_bytes: int = 0
    cost_class: str = "standard"
    priority: str = "normal"
    ttl_seconds: int | None = None
    requires_persistence: bool = False
    audit_required: bool = False
    correlation_ref: str | None = None
    metadata: Json = field(default_factory=dict)

    def queue_key(self) -> str:
        stable = self.idempotency_key or self.request_id or self.correlation_ref or "anonymous"
        return f"{self.work_type}:{self.route_name}:{stable}"


@dataclass(frozen=True)
class AdmissionDecision:
    outcome: AdmissionOutcome
    descriptor: WorkDescriptor
    reason_code: str
    message: str
    retry_after_seconds: int | None = None
    queue_position: int | None = None
    overload_scope: str | None = None
    degraded_to: str | None = None

    def error_body(self) -> Json:
        return {
            "error": {
                "code": self.reason_code,
                "message": self.message,
                "tenant_id": self.descriptor.tenant_id,
                "work_type": self.descriptor.work_type,
                "route": self.descriptor.route_name,
                **({"request_id": self.descriptor.request_id} if self.descriptor.request_id else {}),
                **({"retry_after_seconds": self.retry_after_seconds} if self.retry_after_seconds is not None else {}),
                **({"overload_scope": self.overload_scope} if self.overload_scope else {}),
            }
        }


@dataclass(frozen=True)
class AdmissionStats:
    accepted: int
    queued: int
    degraded: int
    rejected: int
    global_overload: int
    dispatched: int
    tenants: list[Json]


class SharedTenantAdmissionController:
    """Shared per-tenant fair admission controller.

    This is still an in-process deterministic implementation. The interface is
    intentionally broader than the current IDE-agent route slice so future work
    can swap in durable queue persistence, distributed counters, metrics, and
    operator controls without changing route handlers.
    """

    def __init__(self, *, default_budget: TenantCapacityBudget, tenant_budgets: dict[str, TenantCapacityBudget] | None = None, global_overload: bool = False, durable_persistence: Any | None = None, telemetry: Any | None = None) -> None:
        self.queue: TenantFairQueue[WorkDescriptor] = TenantFairQueue(default_budget=default_budget, tenant_budgets=tenant_budgets)
        self.global_overload = global_overload
        self.durable_persistence = durable_persistence
        self.telemetry = telemetry
        self._accepted = 0
        self._queued = 0
        self._degraded = 0
        self._rejected = 0
        self._global_overload = 0
        self._dispatched = 0

    def _record_decision(self, decision: AdmissionDecision) -> AdmissionDecision:
        if self.durable_persistence is not None:
            self.durable_persistence.persist_decision(decision)
        if self.telemetry is not None:
            self.telemetry.record_decision(decision)
        return decision

    def admit(self, descriptor: WorkDescriptor) -> AdmissionDecision:
        if self.global_overload:
            self._global_overload += 1
            return self._record_decision(AdmissionDecision(
                outcome=AdmissionOutcome.GLOBAL_OVERLOAD,
                descriptor=descriptor,
                reason_code="global_capacity_exceeded",
                message="global processing capacity is saturated",
                retry_after_seconds=30,
                overload_scope="global",
            ))

        if not self.queue.submit(descriptor.tenant_id, descriptor):
            self._rejected += 1
            return self._record_decision(AdmissionDecision(
                outcome=AdmissionOutcome.REJECTED,
                descriptor=descriptor,
                reason_code="tenant_capacity_exceeded",
                message="tenant processing queue is full",
                retry_after_seconds=10,
                overload_scope="tenant",
            ))

        dispatched = self.queue.dispatch_round()
        self._dispatched += len(dispatched)
        if any(item is descriptor for _tenant_id, item in dispatched):
            self._accepted += 1
            return self._record_decision(AdmissionDecision(
                outcome=AdmissionOutcome.ACCEPTED,
                descriptor=descriptor,
                reason_code="accepted",
                message="work accepted for immediate processing",
            ))

        self._queued += 1
        queue_position = next((row.queued for row in self.queue.stats() if row.tenant_id == descriptor.tenant_id), None)
        return self._record_decision(AdmissionDecision(
            outcome=AdmissionOutcome.QUEUED,
            descriptor=descriptor,
            reason_code="queued_for_fair_dispatch",
            message="work queued behind fair tenant scheduler",
            queue_position=queue_position,
        ))

    def stats(self) -> AdmissionStats:
        return AdmissionStats(
            accepted=self._accepted,
            queued=self._queued,
            degraded=self._degraded,
            rejected=self._rejected,
            global_overload=self._global_overload,
            dispatched=self._dispatched,
            tenants=[row.__dict__ for row in self.queue.stats()],
        )
