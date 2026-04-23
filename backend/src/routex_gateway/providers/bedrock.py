from __future__ import annotations

import asyncio
from typing import Any

import boto3

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


class BedrockAdapter(ProviderAdapter):
    def supports(self, provider: ProviderDefinition) -> bool:
        return provider.kind == ProviderKind.bedrock

    async def chat_completions(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        body = await asyncio.to_thread(
            self._converse,
            provider,
            deployment,
            request,
        )
        content = "".join(
            block.get("text", "")
            for output in body.get("output", {}).get("message", {}).get("content", [])
            for block in [output]
            if block.get("text")
        )
        usage = body.get("usage", {})
        return {
            "id": f"chatcmpl_{deployment.deployment_id}",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": body.get("stopReason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("inputTokens", 0),
                "completion_tokens": usage.get("outputTokens", 0),
                "total_tokens": usage.get("totalTokens", 0),
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
            messages=[OpenAIMessage(role="user", content=str(request.input))],
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
            "Bedrock embeddings are not configured for this deployment",
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

    def _converse(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
    ) -> dict[str, Any]:
        region = deployment.region or provider.metadata.get("region") or "us-east-1"
        client = boto3.client("bedrock-runtime", region_name=region)
        try:
            return client.converse(
                modelId=deployment.upstream_model,
                messages=[
                    {
                        "role": "assistant" if message.role == "assistant" else "user",
                        "content": [{"text": _message_text(message)}],
                    }
                    for message in request.messages
                    if message.role != "system"
                ],
                system=[
                    {"text": _message_text(message)}
                    for message in request.messages
                    if message.role == "system" and _message_text(message)
                ],
                inferenceConfig={
                    "maxTokens": request.max_tokens or 1024,
                    **(
                        {"temperature": request.temperature}
                        if request.temperature is not None
                        else {}
                    ),
                },
            )
        except Exception as exc:  # noqa: BLE001
            raise AdapterExecutionError(
                str(exc),
                status_code=502,
                error_class="upstream_error",
            ) from exc


def _message_text(message: OpenAIMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    if isinstance(message.content, list):
        return "\n".join(
            str(block.get("text", "")) for block in message.content if isinstance(block, dict)
        )
    return ""
