from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from routex_gateway.domain.models import HealthSnapshot, HealthState, ProviderDefinition


class HealthMonitor:
    def __init__(self) -> None:
        self._snapshots: dict[str, HealthSnapshot] = {}

    def apply(self, provider: ProviderDefinition) -> ProviderDefinition:
        result = provider.model_copy(deep=True)
        if provider.provider_id in self._snapshots:
            result.health = deepcopy(self._snapshots[provider.provider_id])
        return result

    def record_success(
        self, provider: ProviderDefinition, latency_ms: float | None
    ) -> ProviderDefinition:
        snapshot = self._snapshots.get(provider.provider_id, deepcopy(provider.health))
        if snapshot.ewma_latency_ms is None:
            snapshot.ewma_latency_ms = latency_ms
        elif latency_ms is not None:
            snapshot.ewma_latency_ms = round(
                (snapshot.ewma_latency_ms * 0.7) + (latency_ms * 0.3), 3
            )
        snapshot.status = HealthState.healthy
        snapshot.error_rate = max(0.0, snapshot.error_rate * 0.8)
        snapshot.last_checked_at = datetime.now(UTC)
        snapshot.cooldown_until = None
        self._snapshots[provider.provider_id] = snapshot
        return self.apply(provider)

    def record_failure(
        self, provider: ProviderDefinition, *, severe: bool = False
    ) -> ProviderDefinition:
        snapshot = self._snapshots.get(provider.provider_id, deepcopy(provider.health))
        snapshot.status = HealthState.down if severe else HealthState.degraded
        snapshot.error_rate = min(1.0, snapshot.error_rate + (0.5 if severe else 0.2))
        snapshot.last_checked_at = datetime.now(UTC)
        snapshot.cooldown_until = datetime.now(UTC) + timedelta(seconds=30 if severe else 10)
        self._snapshots[provider.provider_id] = snapshot
        return self.apply(provider)
