from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.domain.models import (
    EndpointKind,
    ProfileDefinition,
    ProjectConfig,
    ProviderDefinition,
    RequestEnvelope,
    RoutedRequest,
    RouteXRequestMetadata,
    RoutingStrategy,
)
from routex_gateway.services.catalog import CatalogService
from routex_gateway.storage.repositories import RuleRepository, TokenRepository


@dataclass
class RequestContext:
    project_id: str | None
    profile_id: str | None
    project_config_path: str | None
    token_name: str | None = None


class RoutingError(RuntimeError):
    pass


class RoutingEngine:
    def __init__(self, catalog: CatalogService) -> None:
        self._catalog = catalog

    async def resolve_context(
        self,
        session: AsyncSession,
        *,
        metadata: RouteXRequestMetadata,
        bearer_token: str | None,
        token_verifier,
    ) -> RequestContext:
        if metadata.project_id:
            return RequestContext(
                project_id=metadata.project_id,
                profile_id=metadata.profile,
                project_config_path=None,
            )

        if bearer_token:
            project_token = await TokenRepository(session).find_by_token(
                bearer_token, token_verifier
            )
            if project_token:
                return RequestContext(
                    project_id=project_token.project_id,
                    profile_id=metadata.profile,
                    project_config_path=project_token.metadata.get("project_config_path"),
                    token_name=project_token.name,
                )

        return RequestContext(
            project_id=None, profile_id=metadata.profile, project_config_path=None
        )

    async def resolve(
        self,
        session: AsyncSession,
        *,
        endpoint: EndpointKind,
        model_alias: str,
        metadata: RouteXRequestMetadata,
        bearer_token: str | None,
        token_verifier,
        project_config_loader=None,
    ) -> RoutedRequest:
        context = await self.resolve_context(
            session,
            metadata=metadata,
            bearer_token=bearer_token,
            token_verifier=token_verifier,
        )
        providers = await self._catalog.list_providers(session)
        profiles = {
            profile.profile_id: profile for profile in await self._catalog.list_profiles(session)
        }
        rules = await RuleRepository(session).list()
        project_config: ProjectConfig | None = None
        if context.project_id and project_config_loader is not None:
            project_config = project_config_loader(context.project_id, context.project_config_path)
            if project_config:
                rules = [*project_config.rules, *rules]

        profile = self._choose_profile(context, profiles, rules, metadata, project_config)
        if project_config and project_config.allow_cloud is not None:
            profile = profile.model_copy(update={"cloud_allowed": project_config.allow_cloud})
        candidates = self._build_candidates(
            providers=providers,
            model_alias=model_alias,
            endpoint=endpoint,
            profile=profile,
            metadata=metadata,
        )
        if not candidates:
            raise RoutingError(f"No deployment available for alias '{model_alias}'")

        deployment, provider = candidates[0]
        fallback_chain = [candidate[0].deployment_id for candidate in candidates]
        envelope = RequestEnvelope(
            endpoint=endpoint,
            model_alias=model_alias,
            profile_id=profile.profile_id,
            project_id=context.project_id,
            provider_id=provider.provider_id,
            deployment_id=deployment.deployment_id,
            fallback_chain=fallback_chain,
            request_metadata={"token_name": context.token_name} if context.token_name else {},
        )
        return RoutedRequest(
            envelope=envelope,
            deployment=deployment,
            provider=provider,
            profile=profile,
            metadata=metadata,
        )

    def _choose_profile(
        self,
        context: RequestContext,
        profiles: dict[str, ProfileDefinition],
        rules,
        metadata: RouteXRequestMetadata,
        project_config: ProjectConfig | None,
    ) -> ProfileDefinition:
        if metadata.privacy_mode and "private-mode" in profiles:
            return profiles["private-mode"]

        requested = metadata.profile or context.profile_id
        if requested and requested in profiles:
            return profiles[requested]
        if project_config and project_config.profile_id and project_config.profile_id in profiles:
            return profiles[project_config.profile_id]

        for rule in sorted(rules, key=lambda item: item.priority):
            if not rule.enabled:
                continue
            if rule.matcher.project_id and rule.matcher.project_id != context.project_id:
                continue
            if rule.action.profile_id and rule.action.profile_id in profiles:
                return profiles[rule.action.profile_id]

        default_profile = self._catalog.snapshot().routex_config.spec.routing.defaultProfile
        return profiles[default_profile]

    def _build_candidates(
        self,
        *,
        providers: list[ProviderDefinition],
        model_alias: str,
        endpoint: EndpointKind,
        profile: ProfileDefinition,
        metadata: RouteXRequestMetadata,
    ) -> list[tuple[Any, ProviderDefinition]]:
        candidate_deployments = set(profile.metadata.get("candidate_deployments") or [])
        candidate_weights = profile.metadata.get("candidate_weights") or {}
        candidate_aliases = set(profile.metadata.get("candidate_aliases") or [])
        enforce_profile_candidates = (
            bool(candidate_deployments) and model_alias in candidate_aliases
        )
        candidates: list[tuple[Any, ProviderDefinition]] = []
        for provider in providers:
            if not provider.enabled:
                continue
            for deployment in provider.deployments:
                if not deployment.enabled or deployment.alias != model_alias:
                    continue
                if endpoint not in deployment.endpoint_kind:
                    continue
                if (
                    metadata.deployment_hint
                    and deployment.deployment_id != metadata.deployment_hint
                ):
                    continue
                if metadata.provider_hint and provider.provider_id != metadata.provider_hint:
                    continue
                if profile.private_mode and not deployment.is_local:
                    continue
                if not profile.cloud_allowed and not deployment.is_local:
                    continue
                if (
                    enforce_profile_candidates
                    and deployment.deployment_id not in candidate_deployments
                ):
                    continue
                candidates.append((deployment, provider))

        def sort_key(item: tuple[Any, ProviderDefinition]) -> tuple[int, int, int]:
            deployment, _provider = item
            local_bonus = 0
            if profile.strategy == RoutingStrategy.local_first and deployment.is_local:
                local_bonus = -100
            if profile.strategy == RoutingStrategy.cloud_power and deployment.is_local:
                local_bonus = 100
            profile_weight = candidate_weights.get(deployment.deployment_id, deployment.weight)
            return (deployment.priority + local_bonus, -profile_weight, -deployment.weight)

        return sorted(candidates, key=sort_key)
