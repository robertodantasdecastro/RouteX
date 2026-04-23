from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.domain.models import (
    ModelAliasDefinition,
    ProfileDefinition,
    ProviderCapabilities,
    ProviderDefinition,
    SettingsDefinition,
)
from routex_gateway.services.manifests import ManifestService, ManifestSnapshot
from routex_gateway.storage.repositories import (
    ProfileRepository,
    ProviderRepository,
    SettingsRepository,
)


class CatalogService:
    def __init__(self, manifests: ManifestService, health_monitor) -> None:
        self._manifests = manifests
        self._health_monitor = health_monitor

    def snapshot(self) -> ManifestSnapshot:
        return self._manifests.get_snapshot()

    async def list_versioned_providers(self) -> list[ProviderDefinition]:
        snapshot = self.snapshot()
        return [deepcopy(provider) for provider in snapshot.providers.values()]

    async def list_override_providers(self, session: AsyncSession) -> list[ProviderDefinition]:
        return await ProviderRepository(session).list()

    async def list_providers(self, session: AsyncSession) -> list[ProviderDefinition]:
        versioned = {
            provider.provider_id: provider for provider in await self.list_versioned_providers()
        }
        overrides = {
            provider.provider_id: provider
            for provider in await self.list_override_providers(session)
        }
        effective: dict[str, ProviderDefinition] = {}
        for provider_id, provider in versioned.items():
            effective[provider_id] = overrides.get(provider_id, provider)
        for provider_id, provider in overrides.items():
            effective.setdefault(provider_id, provider)
        resolved = [self._health_monitor.apply(provider) for provider in effective.values()]
        return sorted(resolved, key=lambda provider: provider.provider_id)

    async def list_versioned_profiles(self) -> list[ProfileDefinition]:
        snapshot = self.snapshot()
        return [deepcopy(profile) for profile in snapshot.profiles.values()]

    async def list_override_profiles(self, session: AsyncSession) -> list[ProfileDefinition]:
        return await ProfileRepository(session).list()

    async def list_profiles(self, session: AsyncSession) -> list[ProfileDefinition]:
        versioned = {
            profile.profile_id: profile for profile in await self.list_versioned_profiles()
        }
        overrides = {
            profile.profile_id: profile for profile in await self.list_override_profiles(session)
        }
        effective: dict[str, ProfileDefinition] = {}
        for profile_id, profile in versioned.items():
            effective[profile_id] = overrides.get(profile_id, profile)
        for profile_id, profile in overrides.items():
            effective.setdefault(profile_id, profile)
        return sorted(effective.values(), key=lambda profile: profile.profile_id)

    async def versioned_settings(self) -> SettingsDefinition:
        return self._manifests.versioned_settings()

    async def effective_settings(self, session: AsyncSession) -> SettingsDefinition:
        override = await SettingsRepository(session).get()
        return override or await self.versioned_settings()

    async def settings_override(self, session: AsyncSession) -> SettingsDefinition | None:
        return await SettingsRepository(session).get()

    async def list_model_aliases(self, session: AsyncSession) -> list[ModelAliasDefinition]:
        providers = await self.list_providers(session)
        grouped = defaultdict(list)
        provider_lookup: dict[str, str] = {}
        caps_by_alias: dict[str, ProviderCapabilities] = {}

        for provider in providers:
            for deployment in provider.deployments:
                if not deployment.enabled:
                    continue
                grouped[deployment.alias].append(deployment)
                provider_lookup.setdefault(deployment.alias, provider.provider_id)
                caps_by_alias.setdefault(deployment.alias, provider.capabilities)

        return [
            ModelAliasDefinition(
                alias=alias,
                display_name=alias,
                deployments=deployments,
                capabilities=caps_by_alias[alias],
                preferred_provider_id=provider_lookup[alias],
            )
            for alias, deployments in sorted(grouped.items())
        ]
