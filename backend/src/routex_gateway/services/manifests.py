from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from routex_gateway.domain.models import (
    AuthKind,
    DeploymentDefinition,
    EndpointKind,
    FallbackPolicy,
    LoggingPolicy,
    ProfileDefinition,
    ProviderCapabilities,
    ProviderDefinition,
    ProviderKind,
    RoutingStrategy,
    SettingsDefinition,
)


class ManifestError(RuntimeError):
    pass


class ManifestMetadata(BaseModel):
    name: str
    owner: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class RouteXGatewaySpec(BaseModel):
    host: str
    port: int
    publicBaseUrl: str
    adminBaseUrl: str


class RouteXRoutingSpec(BaseModel):
    defaultProfile: str
    providerRefs: list[str]
    failoverEnabled: bool
    requestTimeoutMs: int
    retryBudget: int


class RouteXObservabilitySpec(BaseModel):
    auditLogs: bool
    redactSensitiveData: bool
    metricsEnabled: bool
    tracingEnabled: bool


class RouteXConfigSpec(BaseModel):
    environment: str
    gateway: RouteXGatewaySpec
    routing: RouteXRoutingSpec
    observability: RouteXObservabilitySpec


class RouteXConfigDocument(BaseModel):
    apiVersion: str
    kind: Literal["RouteXConfig"]
    metadata: ManifestMetadata
    spec: RouteXConfigSpec


class ProviderEndpointsSpec(BaseModel):
    baseUrl: str | None = None
    region: str | None = None


class ProviderAuthSpec(BaseModel):
    strategy: str
    envVar: str | None = None
    secretRef: str | None = None


class ProviderModelSpec(BaseModel):
    id: str
    alias: str | None = None
    upstreamModel: str | None = None
    purpose: str
    tier: str
    selectorTags: list[str] = Field(default_factory=list)
    enabled: bool = True
    endpoints: list[str] | None = None
    weight: int = 100
    priority: int = 100
    timeoutSeconds: float | None = None
    streamTimeoutSeconds: float | None = None
    region: str | None = None
    isLocal: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderConfigSpec(BaseModel):
    provider: str
    enabled: bool
    endpoints: ProviderEndpointsSpec
    auth: ProviderAuthSpec
    capabilities: list[str]
    models: list[ProviderModelSpec]


class ProviderConfigDocument(BaseModel):
    apiVersion: str
    kind: Literal["ProviderConfig"]
    metadata: ManifestMetadata
    spec: ProviderConfigSpec


class ProfileComplianceSpec(BaseModel):
    pii: str
    dataResidency: str


class ProfileSelectorsSpec(BaseModel):
    capabilities: list[str]
    latencyBudgetMs: int
    budgetClass: str
    compliance: ProfileComplianceSpec
    regionAffinity: str


class ProfileCandidateSpec(BaseModel):
    providerRef: str
    modelRef: str
    weight: int


class RouteProfileSpec(BaseModel):
    goal: str
    description: str | None = None
    strategy: str | None = None
    localPriority: int | None = None
    cloudAllowed: bool | None = None
    privateMode: bool | None = None
    selectors: ProfileSelectorsSpec
    fallbackStrategy: str
    candidates: list[ProfileCandidateSpec]


class RouteProfileDocument(BaseModel):
    apiVersion: str
    kind: Literal["RouteProfile"]
    metadata: ManifestMetadata
    spec: RouteProfileSpec


@dataclass(slots=True)
class ManifestSnapshot:
    routex_config: RouteXConfigDocument
    providers: dict[str, ProviderDefinition]
    profiles: dict[str, ProfileDefinition]
    provider_docs: dict[str, ProviderConfigDocument]
    profile_docs: dict[str, RouteProfileDocument]


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ManifestError(f"{path} must contain a top-level mapping")
    return payload


class ManifestService:
    def __init__(self, config_dir: Path) -> None:
        self._config_dir = config_dir
        self._snapshot: ManifestSnapshot | None = None

    def get_snapshot(self, *, reload: bool = False) -> ManifestSnapshot:
        if self._snapshot is None or reload:
            self._snapshot = self._load_snapshot()
        return self._snapshot

    def _load_snapshot(self) -> ManifestSnapshot:
        defaults_path = self._config_dir / "defaults" / "routex.yaml"
        if not defaults_path.exists():
            raise ManifestError(f"Missing RouteXConfig manifest at {defaults_path}")

        routex_config = RouteXConfigDocument.model_validate(_load_yaml(defaults_path))
        provider_docs = self._load_provider_documents()
        profile_docs = self._load_profile_documents()

        missing_providers = [
            provider_ref
            for provider_ref in routex_config.spec.routing.providerRefs
            if provider_ref not in provider_docs
        ]
        if missing_providers:
            raise ManifestError(
                "RouteXConfig references missing provider manifests: "
                + ", ".join(sorted(missing_providers))
            )

        if routex_config.spec.routing.defaultProfile not in profile_docs:
            raise ManifestError(
                "RouteXConfig references missing default profile: "
                f"{routex_config.spec.routing.defaultProfile}"
            )

        providers = {
            provider_id: self._build_provider_definition(document)
            for provider_id, document in provider_docs.items()
        }
        profiles = {
            profile_id: self._build_profile_definition(document)
            for profile_id, document in profile_docs.items()
        }
        self._attach_profile_candidates(profile_docs, profiles, providers)

        return ManifestSnapshot(
            routex_config=routex_config,
            providers=providers,
            profiles=profiles,
            provider_docs=provider_docs,
            profile_docs=profile_docs,
        )

    def _load_provider_documents(self) -> dict[str, ProviderConfigDocument]:
        result: dict[str, ProviderConfigDocument] = {}
        for path in sorted((self._config_dir / "providers").glob("*.y*ml")):
            document = ProviderConfigDocument.model_validate(_load_yaml(path))
            result[document.metadata.name] = document
        return result

    def _load_profile_documents(self) -> dict[str, RouteProfileDocument]:
        result: dict[str, RouteProfileDocument] = {}
        for path in sorted((self._config_dir / "profiles").glob("*.y*ml")):
            document = RouteProfileDocument.model_validate(_load_yaml(path))
            result[document.metadata.name] = document
        return result

    def _build_provider_definition(self, document: ProviderConfigDocument) -> ProviderDefinition:
        kind = _provider_kind_from_manifest(document.spec.provider)
        auth_kind, secret_ref = _auth_kind_and_secret_ref(document)
        capabilities = _provider_capabilities(document.spec.capabilities)
        provider_id = document.metadata.name
        deployments = [
            _build_deployment(
                provider_id, kind, model, document.spec.endpoints.baseUrl, capabilities
            )
            for model in document.spec.models
        ]

        return ProviderDefinition(
            provider_id=provider_id,
            kind=kind,
            display_name=document.metadata.labels.get("displayName", _titleize(provider_id)),
            enabled=document.spec.enabled,
            auth_kind=auth_kind,
            api_base=document.spec.endpoints.baseUrl,
            secret_ref=secret_ref,
            capabilities=capabilities,
            deployments=deployments,
            metadata={
                "source": "versioned",
                "manifest": provider_id,
                "owner": document.metadata.owner,
                "labels": document.metadata.labels,
            },
        )

    def _build_profile_definition(self, document: RouteProfileDocument) -> ProfileDefinition:
        strategy = _routing_strategy(document)
        private_mode = bool(document.spec.privateMode or strategy == RoutingStrategy.private_mode)
        cloud_allowed = (
            not private_mode if document.spec.cloudAllowed is None else document.spec.cloudAllowed
        )
        local_priority = (
            document.spec.localPriority
            if document.spec.localPriority is not None
            else {
                RoutingStrategy.local_first: 100,
                RoutingStrategy.private_mode: 100,
                RoutingStrategy.cloud_power: 0,
            }.get(strategy, 50)
        )

        profile_id = document.metadata.name
        return ProfileDefinition(
            profile_id=profile_id,
            display_name=document.metadata.labels.get("displayName", _titleize(profile_id)),
            strategy=strategy,
            description=document.spec.description or f"Route profile {profile_id}",
            local_priority=local_priority,
            cloud_allowed=cloud_allowed,
            private_mode=private_mode,
            fallback_policy=FallbackPolicy(
                on_timeout=True,
                on_rate_limit=True,
                on_server_error=True,
                on_context_window=True,
                on_auth_error=False,
            ),
            logging_policy=LoggingPolicy(
                store_prompt_content=False,
                store_response_content=False,
                redact_headers=True,
            ),
            metadata={
                "source": "versioned",
                "manifest": profile_id,
                "goal": document.spec.goal,
                "fallback_strategy": document.spec.fallbackStrategy,
                "selectors": document.spec.selectors.model_dump(mode="json"),
            },
        )

    def _attach_profile_candidates(
        self,
        profile_docs: dict[str, RouteProfileDocument],
        profiles: dict[str, ProfileDefinition],
        providers: dict[str, ProviderDefinition],
    ) -> None:
        lookup: dict[tuple[str, str], DeploymentDefinition] = {}
        for provider in providers.values():
            for deployment in provider.deployments:
                model_ref = deployment.metadata.get("model_ref")
                if model_ref:
                    lookup[(provider.provider_id, model_ref)] = deployment

        for profile_id, document in profile_docs.items():
            candidate_deployments: list[str] = []
            candidate_weights: dict[str, int] = {}
            candidate_aliases: set[str] = set()
            default_alias: str | None = None
            for candidate in document.spec.candidates:
                deployment = lookup.get((candidate.providerRef, candidate.modelRef))
                if deployment is None:
                    raise ManifestError(
                        f"Profile {profile_id} references unknown provider/model pair "
                        f"{candidate.providerRef}/{candidate.modelRef}"
                    )
                candidate_deployments.append(deployment.deployment_id)
                candidate_weights[deployment.deployment_id] = candidate.weight
                candidate_aliases.add(deployment.alias)
                if default_alias is None:
                    default_alias = deployment.alias
            profile = profiles[profile_id]
            profile.metadata["candidate_deployments"] = candidate_deployments
            profile.metadata["candidate_weights"] = candidate_weights
            profile.metadata["candidate_aliases"] = sorted(candidate_aliases)
            profile.metadata["default_model_alias"] = default_alias

    def versioned_settings(self) -> SettingsDefinition:
        snapshot = self.get_snapshot()
        routex_config = snapshot.routex_config
        default_profile = routex_config.spec.routing.defaultProfile
        default_model_alias = snapshot.profiles[default_profile].metadata.get(
            "default_model_alias", "qwen2.5-coder:latest"
        )
        return SettingsDefinition(
            host=routex_config.spec.gateway.host,
            port=routex_config.spec.gateway.port,
            theme="dark",
            startup_enabled=True,
            debug_logging_ttl_minutes=30,
            log_level="INFO",
            default_profile=default_profile,
            cursor_model_alias=str(default_model_alias),
        )


def _provider_kind_from_manifest(value: str) -> ProviderKind:
    normalized = value.replace("-", "_")
    try:
        return ProviderKind(normalized)
    except ValueError as exc:
        raise ManifestError(f"Unsupported provider kind '{value}'") from exc


def _auth_kind_and_secret_ref(document: ProviderConfigDocument) -> tuple[AuthKind, str | None]:
    strategy = document.spec.auth.strategy
    if strategy == "env":
        return AuthKind.bearer, f"env://{document.spec.auth.envVar}"
    if strategy == "secretRef":
        return AuthKind.bearer, document.spec.auth.secretRef
    if strategy == "none":
        return AuthKind.none, None
    if strategy == "aws":
        return AuthKind.aws, "aws://default"
    raise ManifestError(f"Unsupported auth strategy '{strategy}'")


def _provider_capabilities(capabilities: Iterable[str]) -> ProviderCapabilities:
    caps = set(capabilities)
    endpoints: list[EndpointKind] = []
    if "chat" in caps:
        endpoints.append(EndpointKind.chat_completions)
    if "responses" in caps:
        endpoints.append(EndpointKind.responses)
    if "embeddings" in caps:
        endpoints.append(EndpointKind.embeddings)
    return ProviderCapabilities(
        endpoints=endpoints,
        streaming="chat" in caps or "responses" in caps,
        tools="tools" in caps,
        vision="vision" in caps or "images" in caps,
        reasoning_effort="reasoning" in caps or "responses" in caps,
        json_mode="chat" in caps or "responses" in caps,
    )


def _build_deployment(
    provider_id: str,
    provider_kind: ProviderKind,
    model: ProviderModelSpec,
    provider_api_base: str | None,
    provider_capabilities: ProviderCapabilities,
) -> DeploymentDefinition:
    endpoint_kind = (
        [_endpoint_from_manifest(value) for value in model.endpoints]
        if model.endpoints
        else _default_endpoints_for_model(model.purpose, provider_capabilities)
    )
    alias = model.alias or model.upstreamModel or model.id
    upstream_model = model.upstreamModel or model.alias or model.id
    is_local = (
        model.isLocal
        if model.isLocal is not None
        else provider_kind
        in {
            ProviderKind.ollama,
            ProviderKind.lm_studio,
            ProviderKind.mock,
        }
    )
    return DeploymentDefinition(
        deployment_id=f"{provider_id}:{model.id}",
        alias=alias,
        upstream_model=upstream_model,
        provider_id=provider_id,
        endpoint_kind=endpoint_kind,
        enabled=model.enabled,
        weight=model.weight,
        priority=model.priority,
        timeout_seconds=model.timeoutSeconds or 60.0,
        stream_timeout_seconds=model.streamTimeoutSeconds or 120.0,
        api_base=provider_api_base,
        region=model.region,
        is_local=is_local,
        metadata={
            "model_ref": model.id,
            "purpose": model.purpose,
            "tier": model.tier,
            "selector_tags": model.selectorTags,
            **model.metadata,
        },
    )


def _default_endpoints_for_model(
    purpose: str, provider_capabilities: ProviderCapabilities
) -> list[EndpointKind]:
    if purpose == "embeddings":
        return [EndpointKind.embeddings]
    endpoints: list[EndpointKind] = [EndpointKind.chat_completions]
    if EndpointKind.responses in provider_capabilities.endpoints:
        endpoints.append(EndpointKind.responses)
    return endpoints


def _endpoint_from_manifest(value: str) -> EndpointKind:
    mapping = {
        "chat": EndpointKind.chat_completions,
        "chat_completions": EndpointKind.chat_completions,
        "responses": EndpointKind.responses,
        "embeddings": EndpointKind.embeddings,
    }
    if value not in mapping:
        raise ManifestError(f"Unsupported endpoint '{value}'")
    return mapping[value]


def _routing_strategy(document: RouteProfileDocument) -> RoutingStrategy:
    if document.spec.strategy:
        return RoutingStrategy(document.spec.strategy)
    name = document.metadata.name
    if "private" in name:
        return RoutingStrategy.private_mode
    if "local" in name:
        return RoutingStrategy.local_first
    if "cloud" in name:
        return RoutingStrategy.cloud_power
    return RoutingStrategy.balanced


def _titleize(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()
