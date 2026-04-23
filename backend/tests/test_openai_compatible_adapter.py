from __future__ import annotations

import httpx
import pytest
import respx

from routex_gateway.domain.models import (
    AuthKind,
    DeploymentDefinition,
    EndpointKind,
    ProviderCapabilities,
    ProviderDefinition,
    ProviderKind,
)
from routex_gateway.providers.base import AdapterExecutionError
from routex_gateway.providers.openai_compatible import OpenAICompatibleAdapter


def build_provider() -> tuple[ProviderDefinition, DeploymentDefinition]:
    deployment = DeploymentDefinition(
        deployment_id="lmstudio-local:qwen-coder-pentest",
        alias="qwen2.5-coder-3b-pentest",
        upstream_model="qwen2.5-coder-3b-pentest",
        provider_id="lmstudio-local",
        endpoint_kind=[EndpointKind.chat_completions],
        api_base="http://127.0.0.1:1234/v1",
        is_local=True,
    )
    provider = ProviderDefinition(
        provider_id="lmstudio-local",
        kind=ProviderKind.lm_studio,
        display_name="LM Studio Local",
        auth_kind=AuthKind.none,
        api_base="http://127.0.0.1:1234/v1",
        capabilities=ProviderCapabilities(endpoints=[EndpointKind.chat_completions]),
        deployments=[deployment],
    )
    return provider, deployment


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_handles_string_error_payload() -> None:
    provider, deployment = build_provider()
    adapter = OpenAICompatibleAdapter()
    route = respx.post("http://127.0.0.1:1234/v1/chat/completions").mock(
        return_value=httpx.Response(
            500,
            json={
                "error": 'Failed to load model "qwen2.5-coder-3b-pentest". Error: bad state'
            },
        )
    )

    with pytest.raises(AdapterExecutionError) as error:
        await adapter._request(
            provider=provider,
            deployment=deployment,
            endpoint="/chat/completions",
            payload={"model": deployment.upstream_model, "messages": []},
            secret=None,
        )

    assert route.called
    assert error.value.status_code == 500
    assert error.value.error_class == "upstream_error"
    assert "Failed to load model" in str(error.value)


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_handles_nested_error_payload() -> None:
    provider, deployment = build_provider()
    adapter = OpenAICompatibleAdapter()
    respx.post("http://127.0.0.1:1234/v1/chat/completions").mock(
        return_value=httpx.Response(
            404,
            json={"error": {"message": 'model "missing" not found'}},
        )
    )

    with pytest.raises(AdapterExecutionError) as error:
        await adapter._request(
            provider=provider,
            deployment=deployment,
            endpoint="/chat/completions",
            payload={"model": deployment.upstream_model, "messages": []},
            secret=None,
        )

    assert error.value.status_code == 404
    assert 'model "missing" not found' == str(error.value)
