from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.domain.models import RequestLogRecord
from routex_gateway.storage.repositories import RequestLogRepository


class AuditLogger:
    def __init__(self, logs_dir: Path) -> None:
        self._logs_dir = logs_dir
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._jsonl_path = self._logs_dir / "requests.jsonl"

    async def record(self, session: AsyncSession, entry: RequestLogRecord) -> RequestLogRecord:
        sanitized = entry.model_copy(deep=True)
        sanitized.request_metadata = _sanitize_metadata(sanitized.request_metadata)
        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self._jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitized.model_dump(mode="json")) + "\n")
        return await RequestLogRepository(session).create(sanitized)


def _sanitize_metadata(metadata: dict) -> dict:
    return {key: _sanitize_value(key, value) for key, value in metadata.items()}


def _sanitize_value(key: str, value):
    lowered = key.lower()
    if "token" in lowered or "secret" in lowered or "authorization" in lowered:
        return "***redacted***"
    if isinstance(value, dict):
        return {
            nested_key: _sanitize_value(nested_key, nested_value)
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_value(key, item) for item in value]
    return value
