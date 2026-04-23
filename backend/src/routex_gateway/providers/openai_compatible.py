from __future__ import annotations

from typing import Any

import httpx

from routex_gateway.domain.models import (
    AuthKind,
    ChatCompletionsRequest,
    DeploymentDefinition,
    EmbeddingsRequest,
    ProviderDefinition,
    ProviderKind,
    ResponsesRequest,
)
from routex_gateway.providers.base import AdapterExecutionError, ProviderAdapter

OPENAI_COMPATIBLE_PROVIDER_KINDS = {
    ProviderKind.openai,
    ProviderKind.ollama,
    ProviderKind.lm_studio,
}


def _extract_error_message(body: Any, fallback: str) -> str:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message
        if isinstance(error, str) and error.strip():
            return error
        message = body.get("message")
        if isinstance(message, str) and message.strip():
            return message
    elif isinstance(body, str) and body.strip():
        return body
    return fallback


class OpenAICompatibleAdapter(ProviderAdapter):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=120.0)

    def supports(self, provider: ProviderDefinition) -> bool:
        return provider.kind in OPENAI_COMPATIBLE_PROVIDER_KINDS

    async def _request(
        self,
        *,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        endpoint: str,
        payload: dict[str, Any],
        secret: str | None,
    ) -> dict[str, Any]:
        base_url = deployment.api_base or provider.api_base
        if not base_url:
            raise AdapterExecutionError(
                f"Provider {provider.provider_id} is missing api_base",
                status_code=500,
                error_class="provider_config_error",
            )
        if provider.auth_kind == AuthKind.bearer and not secret:
            raise AdapterExecutionError(
                f"Credentials missing for provider {provider.provider_id}",
                status_code=401,
                error_class="credentials_missing",
            )

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"

        response = await self._client.post(
            f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}",
            json=payload,
            headers=headers,
        )
        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:
                body = {"error": {"message": response.text}}
            message = _extract_error_message(body, response.text)
            raise AdapterExecutionError(
                message=message,
                status_code=response.status_code,
                error_class="upstream_error",
            )
        return response.json()

    async def chat_completions(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        payload = request.model_dump(mode="json")
        payload["model"] = deployment.upstream_model
        return await self._request(
            provider=provider,
            deployment=deployment,
            endpoint="/chat/completions",
            payload=payload,
            secret=secret,
        )

    async def responses(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ResponsesRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        payload = request.model_dump(mode="json")
        payload["model"] = deployment.upstream_model
        return await self._request(
            provider=provider,
            deployment=deployment,
            endpoint="/responses",
            payload=payload,
            secret=secret,
        )

    async def embeddings(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: EmbeddingsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        payload = request.model_dump(mode="json")
        payload["model"] = deployment.upstream_model
        return await self._request(
            provider=provider,
            deployment=deployment,
            endpoint="/embeddings",
            payload=payload,
            secret=secret,
        )

    async def list_models(
        self,
        provider: ProviderDefinition,
        secret: str | None,
    ) -> list[dict[str, Any]]:
        base_url = provider.api_base
        if not base_url:
            return []

        headers: dict[str, str] = {}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"

        response = await self._client.get(f"{base_url.rstrip('/')}/models", headers=headers)
        if response.status_code >= 400:
            raise AdapterExecutionError(
                message=response.text,
                status_code=response.status_code,
                error_class="upstream_error",
            )
        body = response.json()
        return body.get("data", [])
