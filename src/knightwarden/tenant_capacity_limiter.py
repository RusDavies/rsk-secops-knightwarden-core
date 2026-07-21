"""Tenant-scoped capacity limiting primitives for local IDE-agent proofs.

The production service still needs framework/worker-pool integration. This module is a
small deterministic model used by regression gates to keep one busy tenant from
monopolizing shared detector/result-envelope capacity.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class TenantCapacityBudget:
    """Per-tenant queue and dispatch budget."""

    max_queued: int
    max_dispatch_per_round: int


@dataclass(frozen=True)
class TenantQueueStats:
    tenant_id: str
    queued: int
    accepted: int
    rejected: int
    dispatched: int


class TenantFairQueue(Generic[T]):
    """Bounded per-tenant queue with round-robin dispatch.

    Items are accepted into tenant-local queues up to `max_queued`. Dispatch then
    walks active tenants in round-robin order and yields at most
    `max_dispatch_per_round` items for a tenant before moving on. This is not a
    distributed rate limiter; it is a fail-closed fairness primitive for route or
    worker-pool adapters to wrap with real clocks, persistence, metrics, and auth.
    """

    def __init__(self, default_budget: TenantCapacityBudget, tenant_budgets: dict[str, TenantCapacityBudget] | None = None) -> None:
        if default_budget.max_queued < 1:
            raise ValueError("default max_queued must be positive")
        if default_budget.max_dispatch_per_round < 1:
            raise ValueError("default max_dispatch_per_round must be positive")
        self._default_budget = default_budget
        self._tenant_budgets = tenant_budgets or {}
        self._queues: dict[str, Deque[T]] = {}
        self._accepted: dict[str, int] = {}
        self._rejected: dict[str, int] = {}
        self._dispatched: dict[str, int] = {}
        self._active_order: Deque[str] = deque()

    def _budget_for(self, tenant_id: str) -> TenantCapacityBudget:
        return self._tenant_budgets.get(tenant_id, self._default_budget)

    def submit(self, tenant_id: str, item: T) -> bool:
        """Submit an item. Return False when the tenant-local queue is full."""
        queue = self._queues.setdefault(tenant_id, deque())
        if len(queue) >= self._budget_for(tenant_id).max_queued:
            self._rejected[tenant_id] = self._rejected.get(tenant_id, 0) + 1
            return False
        was_empty = not queue
        queue.append(item)
        self._accepted[tenant_id] = self._accepted.get(tenant_id, 0) + 1
        if was_empty and tenant_id not in self._active_order:
            self._active_order.append(tenant_id)
        return True

    def dispatch_round(self) -> list[tuple[str, T]]:
        """Dispatch one fair round across currently active tenants."""
        dispatched: list[tuple[str, T]] = []
        tenants_this_round = len(self._active_order)
        for _ in range(tenants_this_round):
            tenant_id = self._active_order.popleft()
            queue = self._queues.get(tenant_id)
            if not queue:
                continue
            budget = self._budget_for(tenant_id)
            for _ in range(min(budget.max_dispatch_per_round, len(queue))):
                item = queue.popleft()
                dispatched.append((tenant_id, item))
                self._dispatched[tenant_id] = self._dispatched.get(tenant_id, 0) + 1
            if queue:
                self._active_order.append(tenant_id)
        return dispatched

    def drain(self, max_rounds: int | None = None) -> list[tuple[str, T]]:
        """Drain queued items fairly, optionally bounded by round count."""
        drained: list[tuple[str, T]] = []
        rounds = 0
        while self._active_order and (max_rounds is None or rounds < max_rounds):
            drained.extend(self.dispatch_round())
            rounds += 1
        return drained

    def stats(self) -> list[TenantQueueStats]:
        tenant_ids = sorted(set(self._queues) | set(self._accepted) | set(self._rejected) | set(self._dispatched))
        return [
            TenantQueueStats(
                tenant_id=tenant_id,
                queued=len(self._queues.get(tenant_id, ())),
                accepted=self._accepted.get(tenant_id, 0),
                rejected=self._rejected.get(tenant_id, 0),
                dispatched=self._dispatched.get(tenant_id, 0),
            )
            for tenant_id in tenant_ids
        ]

    @property
    def active_tenants(self) -> Iterable[str]:
        return tuple(self._active_order)
