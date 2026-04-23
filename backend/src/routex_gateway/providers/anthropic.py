from __future__ import annotations

from typing import Any

import httpx

from routex_gateway.domain.models import (
    ChatCompletionsRequest,
    DeploymentDefinition,
    EmbeddingsRequest,
    OpenAIMessage,
    ProviderDefinition,
    ProviderKind,
    ResponsesRequest,
)
from routex_gateway.providers.base import AdapterExecutionError, ProviderAdapter


class AnthropicAdapter(ProviderAdapter):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=120.0)

    def supports(self, provider: ProviderDefinition) -> bool:
        return provider.kind == ProviderKind.anthropic

    async def chat_completions(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        if not secret:
            raise AdapterExecutionError(
                "Anthropic API key is missing",
                status_code=401,
                error_class="credentials_missing",
            )
        payload = {
            "model": deployment.upstream_model,
            "max_tokens": request.max_tokens or 1024,
            "messages": [
                _anthropic_message(message)
                for message in request.messages
                if message.role != "system"
            ],
            "system": "\n".join(
                _message_text(message)
                for message in request.messages
                if message.role == "system" and _message_text(message)
            )
            or None,
            "temperature": request.temperature,
            "stream": False,
        }
        response = await self._client.post(
            f"{provider.api_base.rstrip('/')}/v1/messages",
            json=payload,
            headers={
                "x-api-key": secret,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        if response.status_code >= 400:
            raise AdapterExecutionError(
                response.text,
                status_code=response.status_code,
                error_class="upstream_error",
            )
        body = response.json()
        content = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        return {
            "id": body.get("id", f"chatcmpl_{deployment.deployment_id}"),
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": body.get("stop_reason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": body.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": body.get("usage", {}).get("output_tokens", 0),
                "total_tokens": body.get("usage", {}).get("input_tokens", 0)
                + body.get("usage", {}).get("output_tokens", 0),
            },
        }

    async def responses(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ResponsesRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        chat_request = ChatCompletionsRequest(
            model=request.model,
            messages=[OpenAIMessage(role="user", content=_coerce_input_text(request.input))],
            metadata=request.metadata,
        )
        chat_response = await self.chat_completions(provider, deployment, chat_request, secret)
        return {
            "id": chat_response["id"].replace("chatcmpl", "resp"),
            "object": "response",
            "status": "completed",
            "model": request.model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": chat_response["choices"][0]["message"]["content"],
                        }
                    ],
                }
            ],
        }

    async def embeddings(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: EmbeddingsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        raise AdapterExecutionError(
            "Anthropic embeddings are not configured for this deployment",
            status_code=400,
            error_class="unsupported_endpoint",
        )

    async def list_models(
        self,
        provider: ProviderDefinition,
        secret: str | None,
    ) -> list[dict[str, Any]]:
        return [
            {"id": deployment.alias, "object": "model", "owned_by": provider.provider_id}
            for deployment in provider.deployments
        ]


def _anthropic_message(message: OpenAIMessage) -> dict[str, Any]:
    return {
        "role": "assistant" if message.role == "assistant" else "user",
        "content": [{"type": "text", "text": _message_text(message)}],
    }


def _message_text(message: OpenAIMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    if isinstance(message.content, list):
        return "\n".join(
            str(block.get("text", "")) for block in message.content if isinstance(block, dict)
        )
    return ""


def _coerce_input_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)
