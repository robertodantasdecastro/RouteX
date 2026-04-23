from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.domain.models import (
    ProfileDefinition,
    ProjectToken,
    ProviderDefinition,
    RequestLogRecord,
    RuleDefinition,
    SettingsDefinition,
)
from routex_gateway.storage.models import (
    ProfileRecord,
    ProjectTokenRecord,
    ProviderRecord,
    RequestLogRow,
    RuleRecord,
    SettingsRecord,
)


class ProviderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ProviderDefinition]:
        result = await self._session.execute(
            select(ProviderRecord).order_by(ProviderRecord.provider_id)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def upsert(self, provider: ProviderDefinition) -> ProviderDefinition:
        record = await self._session.get(ProviderRecord, provider.provider_id)
        payload = provider.model_dump(mode="json")
        if record is None:
            record = ProviderRecord(
                provider_id=provider.provider_id,
                kind=provider.kind.value,
                display_name=provider.display_name,
                enabled=provider.enabled,
                secret_ref=provider.secret_ref,
                data=payload,
            )
            self._session.add(record)
        else:
            record.kind = provider.kind.value
            record.display_name = provider.display_name
            record.enabled = provider.enabled
            record.secret_ref = provider.secret_ref
            record.data = payload
        await self._session.flush()
        return provider

    async def delete(self, provider_id: str) -> None:
        record = await self._session.get(ProviderRecord, provider_id)
        if record is not None:
            await self._session.delete(record)

    def _to_domain(self, row: ProviderRecord) -> ProviderDefinition:
        return ProviderDefinition.model_validate(row.data)


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ProfileDefinition]:
        result = await self._session.execute(
            select(ProfileRecord).order_by(ProfileRecord.profile_id)
        )
        return [ProfileDefinition.model_validate(row.data) for row in result.scalars().all()]

    async def upsert(self, profile: ProfileDefinition) -> ProfileDefinition:
        record = await self._session.get(ProfileRecord, profile.profile_id)
        payload = profile.model_dump(mode="json")
        if record is None:
            record = ProfileRecord(
                profile_id=profile.profile_id,
                display_name=profile.display_name,
                enabled=True,
                data=payload,
            )
            self._session.add(record)
        else:
            record.display_name = profile.display_name
            record.data = payload
        await self._session.flush()
        return profile


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[RuleDefinition]:
        result = await self._session.execute(
            select(RuleRecord).order_by(RuleRecord.priority, RuleRecord.rule_id)
        )
        return [RuleDefinition.model_validate(row.data) for row in result.scalars().all()]

    async def upsert(self, rule: RuleDefinition) -> RuleDefinition:
        record = await self._session.get(RuleRecord, rule.rule_id)
        payload = rule.model_dump(mode="json")
        if record is None:
            record = RuleRecord(
                rule_id=rule.rule_id,
                name=rule.name,
                priority=rule.priority,
                enabled=rule.enabled,
                data=payload,
            )
            self._session.add(record)
        else:
            record.name = rule.name
            record.priority = rule.priority
            record.enabled = rule.enabled
            record.data = payload
        await self._session.flush()
        return rule


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ProjectToken]:
        result = await self._session.execute(
            select(ProjectTokenRecord).order_by(ProjectTokenRecord.created_at.desc())
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def create(self, token: ProjectToken) -> ProjectToken:
        record = ProjectTokenRecord(
            token_id=token.token_id,
            project_id=token.project_id,
            name=token.name,
            token_preview=token.token_preview,
            token_hash=token.token_hash,
            data=token.metadata,
        )
        self._session.add(record)
        await self._session.flush()
        return token

    async def find_by_token(self, plaintext: str, verifier) -> ProjectToken | None:
        candidates: Sequence[ProjectTokenRecord]
        result = await self._session.execute(select(ProjectTokenRecord))
        candidates = result.scalars().all()
        for row in candidates:
            if verifier(plaintext, row.token_hash):
                domain = self._to_domain(row)
                row.last_used_at = datetime.now(UTC)
                await self._session.flush()
                return domain
        return None

    def _to_domain(self, row: ProjectTokenRecord) -> ProjectToken:
        return ProjectToken(
            token_id=row.token_id,
            project_id=row.project_id,
            name=row.name,
            token_preview=row.token_preview,
            token_hash=row.token_hash,
            created_at=row.created_at,
            last_used_at=row.last_used_at,
            metadata=row.data,
        )


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SettingsDefinition | None:
        row = await self._session.get(SettingsRecord, "singleton")
        if row is None:
            return None
        return SettingsDefinition.model_validate(row.data)

    async def upsert(self, settings: SettingsDefinition) -> SettingsDefinition:
        row = await self._session.get(SettingsRecord, "singleton")
        payload = settings.model_dump(mode="json")
        if row is None:
            row = SettingsRecord(settings_id="singleton", data=payload)
            self._session.add(row)
        else:
            row.data = payload
        await self._session.flush()
        return settings


class RequestLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: RequestLogRecord) -> RequestLogRecord:
        row = RequestLogRow(
            request_id=record.request_id,
            endpoint=record.endpoint.value,
            status=record.status,
            model_alias=record.model_alias,
            project_id=record.project_id,
            profile_id=record.profile_id,
            provider_id=record.provider_id,
            deployment_id=record.deployment_id,
            latency_ms=record.latency_ms,
            ttft_ms=record.ttft_ms,
            error_class=record.error_class,
            fallback_chain=record.fallback_chain,
            request_metadata=record.request_metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return record

    async def list_recent(self, limit: int = 50) -> list[RequestLogRecord]:
        statement: Select[tuple[RequestLogRow]] = (
            select(RequestLogRow).order_by(RequestLogRow.created_at.desc()).limit(limit)
        )
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [
            RequestLogRecord(
                request_id=row.request_id,
                endpoint=row.endpoint,
                status=row.status,
                model_alias=row.model_alias,
                project_id=row.project_id,
                profile_id=row.profile_id,
                provider_id=row.provider_id,
                deployment_id=row.deployment_id,
                latency_ms=row.latency_ms,
                ttft_ms=row.ttft_ms,
                error_class=row.error_class,
                fallback_chain=row.fallback_chain,
                created_at=row.created_at,
                request_metadata=row.request_metadata,
            )
            for row in rows
        ]
