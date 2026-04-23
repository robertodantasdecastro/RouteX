from __future__ import annotations

from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.storage.repositories import RequestLogRepository


class MetricsService:
    async def snapshot(self, session: AsyncSession) -> dict:
        requests = await RequestLogRepository(session).list_recent(limit=500)
        by_status = Counter(record.status for record in requests)
        by_provider = Counter(record.provider_id or "unknown" for record in requests)
        by_error_class = Counter(record.error_class or "none" for record in requests)
        cooldowns = Counter(
            "cooldown" if record.request_metadata.get("cooldown_applied") else "none"
            for record in requests
        )
        return {
            "request_count": len(requests),
            "by_status": dict(by_status),
            "by_provider": dict(by_provider),
            "by_error_class": dict(by_error_class),
            "cooldown_events": dict(cooldowns),
            "recent_requests": [record.model_dump(mode="json") for record in requests[:20]],
        }
