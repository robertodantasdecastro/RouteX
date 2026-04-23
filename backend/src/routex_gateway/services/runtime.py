from __future__ import annotations

from time import monotonic
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from routex_gateway.core.config import AppSettings
from routex_gateway.domain.models import (
    ChatCompletionsRequest,
    EmbeddingsRequest,
    EndpointKind,
    HealthResponse,
    RequestLogRecord,
    ResponsesRequest,
    RoutedRequest,
    RouteXRequestMetadata,
)
from routex_gateway.observability.audit import AuditLogger
from routex_gateway.providers.anthropic import AnthropicAdapter
from routex_gateway.providers.base import AdapterExecutionError, ProviderAdapter
from routex_gateway.providers.bedrock import BedrockAdapter
from routex_gateway.providers.mock import MockProviderAdapter
from routex_gateway.providers.openai_compatible import OpenAICompatibleAdapter
from routex_gateway.security.tokens import TokenManager
from routex_gateway.services.catalog import CatalogService
from routex_gateway.services.credentials import CredentialsManager
from routex_gateway.services.health import HealthMonitor
from routex_gateway.services.manifests import ManifestService
from routex_gateway.services.metrics import MetricsService
from routex_gateway.services.project_configs import ProjectConfigService
from routex_gateway.services.routing import RoutingEngine, RoutingError
from routex_gateway.storage.repositories import RuleRepository


class RouteXRuntime:
    def __init__(
        self, settings: AppSettings, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.health = HealthMonitor()
        self.manifests = ManifestService(settings.config_dir)
        self.manifests.get_snapshot()
        self.catalog = CatalogService(self.manifests, self.health)
        self.routing = RoutingEngine(self.catalog)
        self.credentials = CredentialsManager()
        self.audit = AuditLogger(settings.logs_dir)
        self.metrics = MetricsService()
        self.tokens = TokenManager()
        self.project_configs = ProjectConfigService(settings)
        self.adapters: list[ProviderAdapter] = [
            MockProviderAdapter(),
            OpenAICompatibleAdapter(),
            AnthropicAdapter(),
            BedrockAdapter(),
        ]
        self.started_at = monotonic()

    def uptime_seconds(self) -> int:
        return int(monotonic() - self.started_at)

    def adapter_for(self, provider) -> ProviderAdapter:
        for adapter in self.adapters:
            if adapter.supports(provider):
                return adapter
        raise RoutingError(f"No adapter registered for provider kind '{provider.kind}'")

    @staticmethod
    def parse_metadata(raw: dict[str, Any]) -> RouteXRequestMetadata:
        return RouteXRequestMetadata.model_validate(raw.get("routex", {}))

    async def execute_chat(
        self,
        session: AsyncSession,
        request: ChatCompletionsRequest,
        bearer_token: str | None,
    ) -> dict[str, Any]:
        return await self._execute(
            session=session,
            endpoint=EndpointKind.chat_completions,
            model_alias=request.model,
            metadata=self.parse_metadata(request.metadata),
            bearer_token=bearer_token,
            payload=request,
        )

    async def execute_responses(
        self,
        session: AsyncSession,
        request: ResponsesRequest,
        bearer_token: str | None,
    ) -> dict[str, Any]:
        return await self._execute(
            session=session,
            endpoint=EndpointKind.responses,
            model_alias=request.model,
            metadata=self.parse_metadata(request.metadata),
            bearer_token=bearer_token,
            payload=request,
        )

    async def execute_embeddings(
        self,
        session: AsyncSession,
        request: EmbeddingsRequest,
        bearer_token: str | None,
    ) -> dict[str, Any]:
        return await self._execute(
            session=session,
            endpoint=EndpointKind.embeddings,
            model_alias=request.model,
            metadata=self.parse_metadata(request.metadata),
            bearer_token=bearer_token,
            payload=request,
        )

    async def _execute(
        self,
        *,
        session: AsyncSession,
        endpoint: EndpointKind,
        model_alias: str,
        metadata: RouteXRequestMetadata,
        bearer_token: str | None,
        payload,
    ) -> dict[str, Any]:
        routed = await self.routing.resolve(
            session,
            endpoint=endpoint,
            model_alias=model_alias,
            metadata=metadata,
            bearer_token=bearer_token,
            token_verifier=self.tokens.verify,
            project_config_loader=self.project_configs.load_for_project,
        )

        fallback_chain = routed.envelope.fallback_chain
        providers = await self.catalog.list_providers(session)
        provider_map = {provider.provider_id: provider for provider in providers}

        last_error: AdapterExecutionError | None = None
        cooldown_applied = False
        for deployment_id in fallback_chain:
            candidate = self._reroute_candidate(routed, provider_map, deployment_id)
            if candidate is None:
                continue
            start = monotonic()
            try:
                secret = await self.credentials.resolve_secret(candidate.provider)
                adapter = self.adapter_for(candidate.provider)
                if endpoint == EndpointKind.chat_completions:
                    response = await adapter.chat_completions(
                        candidate.provider, candidate.deployment, payload, secret
                    )
                elif endpoint == EndpointKind.responses:
                    response = await adapter.responses(
                        candidate.provider, candidate.deployment, payload, secret
                    )
                else:
                    response = await adapter.embeddings(
                        candidate.provider, candidate.deployment, payload, secret
                    )
                latency_ms = (monotonic() - start) * 1000
                self.health.record_success(candidate.provider, latency_ms)
                await self.audit.record(
                    session,
                    RequestLogRecord(
                        request_id=candidate.envelope.request_id,
                        endpoint=endpoint,
                        status="success",
                        model_alias=model_alias,
                        project_id=candidate.envelope.project_id,
                        profile_id=candidate.profile.profile_id,
                        provider_id=candidate.provider.provider_id,
                        deployment_id=candidate.deployment.deployment_id,
                        latency_ms=latency_ms,
                        ttft_ms=latency_ms,
                        fallback_chain=fallback_chain,
                        request_metadata=candidate.envelope.request_metadata,
                    ),
                )
                await session.commit()
                return response
            except AdapterExecutionError as exc:
                last_error = exc
                severe = exc.status_code >= 500 or exc.status_code == 429
                self.health.record_failure(candidate.provider, severe=severe)
                cooldown_applied = cooldown_applied or severe
                if exc.status_code in {401, 403}:
                    break

        await self.audit.record(
            session,
            RequestLogRecord(
                request_id=routed.envelope.request_id,
                endpoint=endpoint,
                status="error",
                model_alias=model_alias,
                project_id=routed.envelope.project_id,
                profile_id=routed.profile.profile_id,
                provider_id=routed.provider.provider_id,
                deployment_id=routed.deployment.deployment_id,
                error_class=last_error.error_class if last_error else "routing_error",
                fallback_chain=fallback_chain,
                request_metadata={
                    **routed.envelope.request_metadata,
                    "cooldown_applied": cooldown_applied,
                },
            ),
        )
        await session.commit()
        if last_error:
            raise last_error
        raise RoutingError(f"No candidate deployment succeeded for alias '{model_alias}'")

    async def health_payload(self, session: AsyncSession) -> HealthResponse:
        providers = await self.catalog.list_providers(session)
        profiles = await self.catalog.list_profiles(session)
        settings = await self.catalog.effective_settings(session)
        return HealthResponse(
            app=self.settings.app_name,
            version="0.2.0-alpha",
            uptime_seconds=self.uptime_seconds(),
            host=settings.host,
            port=settings.port,
            providers=providers,
            profiles=profiles,
            settings=settings,
        )

    async def control_plane_bundle(self, session: AsyncSession) -> dict[str, Any]:
        versioned_providers = await self.catalog.list_versioned_providers()
        override_providers = await self.catalog.list_override_providers(session)
        effective_providers = await self.catalog.list_providers(session)
        versioned_profiles = await self.catalog.list_versioned_profiles()
        override_profiles = await self.catalog.list_override_profiles(session)
        effective_profiles = await self.catalog.list_profiles(session)
        versioned_settings = await self.catalog.versioned_settings()
        override_settings = await self.catalog.settings_override(session)
        effective_settings = await self.catalog.effective_settings(session)
        overrides_rules = await RuleRepository(session).list()
        return {
            "providers": {
                "versioned": [item.model_dump(mode="json") for item in versioned_providers],
                "overrides": [item.model_dump(mode="json") for item in override_providers],
                "effective": [item.model_dump(mode="json") for item in effective_providers],
            },
            "profiles": {
                "versioned": [item.model_dump(mode="json") for item in versioned_profiles],
                "overrides": [item.model_dump(mode="json") for item in override_profiles],
                "effective": [item.model_dump(mode="json") for item in effective_profiles],
            },
            "rules": {
                "versioned": [],
                "overrides": [item.model_dump(mode="json") for item in overrides_rules],
                "effective": [item.model_dump(mode="json") for item in overrides_rules],
            },
            "settings": {
                "versioned": versioned_settings.model_dump(mode="json"),
                "override": override_settings.model_dump(mode="json")
                if override_settings
                else None,
                "effective": effective_settings.model_dump(mode="json"),
            },
            "config": self.catalog.snapshot().routex_config.model_dump(mode="json"),
        }

    async def route_preview(
        self,
        session: AsyncSession,
        *,
        model_alias: str,
        profile_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        routed = await self.routing.resolve(
            session,
            endpoint=EndpointKind.chat_completions,
            model_alias=model_alias,
            metadata=RouteXRequestMetadata(profile=profile_id, project_id=project_id),
            bearer_token=None,
            token_verifier=self.tokens.verify,
            project_config_loader=self.project_configs.load_for_project,
        )
        return {
            "request_id": routed.envelope.request_id,
            "model_alias": model_alias,
            "project_id": routed.envelope.project_id,
            "profile_id": routed.profile.profile_id,
            "selected_provider": routed.provider.provider_id,
            "selected_deployment": routed.deployment.deployment_id,
            "fallback_chain": routed.envelope.fallback_chain,
        }

    def _reroute_candidate(
        self,
        routed: RoutedRequest,
        provider_map: dict[str, Any],
        deployment_id: str,
    ) -> RoutedRequest | None:
        for provider in provider_map.values():
            for deployment in provider.deployments:
                if deployment.deployment_id == deployment_id:
                    return RoutedRequest(
                        envelope=routed.envelope.model_copy(
                            update={
                                "provider_id": provider.provider_id,
                                "deployment_id": deployment.deployment_id,
                            }
                        ),
                        deployment=deployment,
                        provider=provider,
                        profile=routed.profile,
                        metadata=routed.metadata,
                    )
        return None
