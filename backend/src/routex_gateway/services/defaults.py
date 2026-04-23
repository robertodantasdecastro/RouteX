from __future__ import annotations

from routex_gateway.domain.models import (
    AuthKind,
    DeploymentDefinition,
    EndpointKind,
    ProfileDefinition,
    ProviderCapabilities,
    ProviderDefinition,
    ProviderKind,
    RoutingStrategy,
    RuleAction,
    RuleDefinition,
    RuleMatcher,
)


def default_profiles() -> list[ProfileDefinition]:
    return [
        ProfileDefinition(
            profile_id="local-first",
            display_name="Local First",
            strategy=RoutingStrategy.local_first,
            description="Prioriza LM Studio/Ollama e evita cloud sempre que possivel.",
            local_priority=100,
            cloud_allowed=True,
        ),
        ProfileDefinition(
            profile_id="balanced",
            display_name="Balanced",
            strategy=RoutingStrategy.balanced,
            description="Equilibra latencia, saude e disponibilidade.",
            local_priority=50,
            cloud_allowed=True,
        ),
        ProfileDefinition(
            profile_id="cloud-power",
            display_name="Cloud Power",
            strategy=RoutingStrategy.cloud_power,
            description="Prioriza frontier models na nuvem.",
            local_priority=0,
            cloud_allowed=True,
        ),
        ProfileDefinition(
            profile_id="private-mode",
            display_name="Private Mode",
            strategy=RoutingStrategy.private_mode,
            description="Bloqueia qualquer envio para provedores remotos.",
            local_priority=100,
            cloud_allowed=False,
            private_mode=True,
        ),
    ]


def default_rules() -> list[RuleDefinition]:
    return [
        RuleDefinition(
            rule_id="default-balanced",
            name="Default Balanced",
            priority=1000,
            matcher=RuleMatcher(),
            action=RuleAction(profile_id="balanced"),
        )
    ]


def default_providers() -> list[ProviderDefinition]:
    common_caps = ProviderCapabilities(
        endpoints=[
            EndpointKind.chat_completions,
            EndpointKind.responses,
            EndpointKind.embeddings,
        ],
        streaming=True,
        tools=True,
        reasoning_effort=True,
        json_mode=True,
    )
    return [
        ProviderDefinition(
            provider_id="mock-local",
            kind=ProviderKind.mock,
            display_name="Mock Local",
            auth_kind=AuthKind.none,
            capabilities=common_caps,
            deployments=[
                DeploymentDefinition(
                    deployment_id="mock-gpt-4.1-mini",
                    alias="gpt-4.1-mini",
                    upstream_model="gpt-4.1-mini",
                    provider_id="mock-local",
                    endpoint_kind=common_caps.endpoints,
                    weight=100,
                    priority=50,
                    is_local=True,
                ),
                DeploymentDefinition(
                    deployment_id="mock-gpt-5-codex",
                    alias="gpt-5.2-codex",
                    upstream_model="gpt-5.2-codex",
                    provider_id="mock-local",
                    endpoint_kind=common_caps.endpoints,
                    weight=100,
                    priority=50,
                    is_local=True,
                ),
            ],
        ),
        ProviderDefinition(
            provider_id="openai-cloud",
            kind=ProviderKind.openai,
            display_name="OpenAI",
            auth_kind=AuthKind.bearer,
            api_base="https://api.openai.com/v1",
            secret_ref="keychain://routex/providers/openai-cloud",
            capabilities=common_caps,
            deployments=[
                DeploymentDefinition(
                    deployment_id="openai-gpt-4.1-mini",
                    alias="gpt-4.1-mini",
                    upstream_model="gpt-4.1-mini",
                    provider_id="openai-cloud",
                    endpoint_kind=common_caps.endpoints,
                    weight=100,
                    priority=100,
                ),
                DeploymentDefinition(
                    deployment_id="openai-gpt-5.2-codex",
                    alias="gpt-5.2-codex",
                    upstream_model="gpt-5.2-codex",
                    provider_id="openai-cloud",
                    endpoint_kind=common_caps.endpoints,
                    weight=100,
                    priority=100,
                ),
            ],
        ),
        ProviderDefinition(
            provider_id="ollama-local",
            kind=ProviderKind.ollama,
            display_name="Ollama",
            auth_kind=AuthKind.none,
            api_base="http://127.0.0.1:11434/v1",
            capabilities=common_caps,
            deployments=[
                DeploymentDefinition(
                    deployment_id="ollama-qwen-coder",
                    alias="qwen2.5-coder:latest",
                    upstream_model="qwen2.5-coder:latest",
                    provider_id="ollama-local",
                    endpoint_kind=common_caps.endpoints,
                    weight=100,
                    priority=10,
                    is_local=True,
                )
            ],
        ),
    ]
