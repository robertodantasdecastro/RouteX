from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProviderKind(StrEnum):
    openai = "openai"
    anthropic = "anthropic"
    bedrock = "bedrock"
    ollama = "ollama"
    lm_studio = "lm_studio"
    mock = "mock"


class RoutingStrategy(StrEnum):
    manual = "manual"
    balanced = "balanced"
    local_first = "local_first"
    cloud_power = "cloud_power"
    private_mode = "private_mode"


class HealthState(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    down = "down"


class AuthKind(StrEnum):
    bearer = "bearer"
    aws = "aws"
    none = "none"


class EndpointKind(StrEnum):
    chat_completions = "chat_completions"
    responses = "responses"
    embeddings = "embeddings"


class HealthSnapshot(BaseModel):
    status: HealthState = HealthState.healthy
    ewma_latency_ms: float | None = None
    error_rate: float = 0.0
    last_checked_at: datetime | None = None
    cooldown_until: datetime | None = None


class FallbackPolicy(BaseModel):
    on_timeout: bool = True
    on_rate_limit: bool = True
    on_server_error: bool = True
    on_context_window: bool = True
    on_auth_error: bool = False


class LoggingPolicy(BaseModel):
    store_prompt_content: bool = False
    store_response_content: bool = False
    redact_headers: bool = True
    debug_until: datetime | None = None


class ProviderCapabilities(BaseModel):
    endpoints: list[EndpointKind] = Field(default_factory=list)
    streaming: bool = True
    tools: bool = False
    vision: bool = False
    reasoning_effort: bool = False
    json_mode: bool = False


class DeploymentDefinition(BaseModel):
    deployment_id: str
    alias: str
    upstream_model: str
    provider_id: str
    endpoint_kind: list[EndpointKind] = Field(default_factory=list)
    enabled: bool = True
    weight: int = 100
    priority: int = 100
    timeout_seconds: float = 60.0
    stream_timeout_seconds: float = 120.0
    api_base: str | None = None
    region: str | None = None
    is_local: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderDefinition(BaseModel):
    provider_id: str
    kind: ProviderKind
    display_name: str
    enabled: bool = True
    auth_kind: AuthKind = AuthKind.bearer
    api_base: str | None = None
    secret_ref: str | None = None
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)
    deployments: list[DeploymentDefinition] = Field(default_factory=list)
    health: HealthSnapshot = Field(default_factory=HealthSnapshot)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelAliasDefinition(BaseModel):
    alias: str
    display_name: str
    deployments: list[DeploymentDefinition] = Field(default_factory=list)
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)
    preferred_provider_id: str | None = None


class ProfileDefinition(BaseModel):
    profile_id: str
    display_name: str
    strategy: RoutingStrategy
    description: str
    local_priority: int = 50
    cloud_allowed: bool = True
    private_mode: bool = False
    fallback_policy: FallbackPolicy = Field(default_factory=FallbackPolicy)
    logging_policy: LoggingPolicy = Field(default_factory=LoggingPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleAction(BaseModel):
    profile_id: str | None = None
    deployment_hint: str | None = None
    provider_hint: str | None = None
    allow_cloud: bool | None = None
    force_private_mode: bool | None = None


class RuleMatcher(BaseModel):
    project_id: str | None = None
    path_prefix: str | None = None
    model_alias: str | None = None


class RuleDefinition(BaseModel):
    rule_id: str
    name: str
    enabled: bool = True
    priority: int = 100
    matcher: RuleMatcher = Field(default_factory=RuleMatcher)
    action: RuleAction = Field(default_factory=RuleAction)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectToken(BaseModel):
    token_id: str = Field(default_factory=lambda: f"pt_{uuid4().hex[:12]}")
    project_id: str
    name: str
    token_preview: str
    token_hash: str
    created_at: datetime = Field(default_factory=utc_now)
    last_used_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsDefinition(BaseModel):
    host: str = "127.0.0.1"
    port: int = 48200
    theme: str = "dark"
    startup_enabled: bool = True
    debug_logging_ttl_minutes: int = 30
    log_level: str = "INFO"
    default_profile: str = "balanced"
    cursor_model_alias: str = "qwen2.5-coder:latest"


class ProjectConfig(BaseModel):
    schema_version: str = "1.0"
    project_id: str
    display_name: str | None = None
    profile_id: str | None = None
    allow_cloud: bool | None = None
    default_model_alias: str | None = None
    rules: list[RuleDefinition] = Field(default_factory=list)


class RequestEnvelope(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex}")
    endpoint: EndpointKind
    model_alias: str
    project_id: str | None = None
    profile_id: str | None = None
    provider_id: str | None = None
    deployment_id: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    request_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class RequestLogRecord(BaseModel):
    request_id: str
    endpoint: EndpointKind
    status: str
    model_alias: str
    project_id: str | None = None
    profile_id: str | None = None
    provider_id: str | None = None
    deployment_id: str | None = None
    latency_ms: float | None = None
    ttft_ms: float | None = None
    error_class: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    request_metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    app: str
    version: str
    uptime_seconds: int
    host: str
    port: int
    providers: list[ProviderDefinition]
    profiles: list[ProfileDefinition]
    settings: SettingsDefinition


class OpenAIMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None


class RouteXRequestMetadata(BaseModel):
    profile: str | None = None
    project_id: str | None = None
    deployment_hint: str | None = None
    provider_hint: str | None = None
    privacy_mode: bool | None = None


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: list[OpenAIMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponsesRequest(BaseModel):
    model: str
    input: Any
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingsRequest(BaseModel):
    model: str
    input: str | list[str]
    encoding_format: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutedRequest(BaseModel):
    envelope: RequestEnvelope
    deployment: DeploymentDefinition
    provider: ProviderDefinition
    profile: ProfileDefinition
    metadata: RouteXRequestMetadata = Field(default_factory=RouteXRequestMetadata)
