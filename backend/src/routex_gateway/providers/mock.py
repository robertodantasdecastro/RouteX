from __future__ import annotations

from typing import Any

from routex_gateway.domain.models import (
    ChatCompletionsRequest,
    DeploymentDefinition,
    EmbeddingsRequest,
    ProviderDefinition,
    ProviderKind,
    ResponsesRequest,
)
from routex_gateway.providers.base import ProviderAdapter


class MockProviderAdapter(ProviderAdapter):
    def supports(self, provider: ProviderDefinition) -> bool:
        return provider.kind == ProviderKind.mock

    async def chat_completions(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        prompt_preview = request.messages[-1].content if request.messages else ""
        return {
            "id": f"chatcmpl_mock_{deployment.deployment_id}",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            f"RouteX mock response via {provider.display_name} "
                            f"for deployment {deployment.deployment_id}. "
                            f"Prompt preview: {prompt_preview}"
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 16, "completion_tokens": 24, "total_tokens": 40},
        }

    async def responses(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ResponsesRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        return {
            "id": f"resp_mock_{deployment.deployment_id}",
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
                            "text": f"RouteX mock response for {deployment.alias}",
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
        items = request.input if isinstance(request.input, list) else [request.input]
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": index,
                    "embedding": [float(index), 0.1, 0.2, 0.3],
                }
                for index, _ in enumerate(items)
            ],
            "model": request.model,
            "usage": {"prompt_tokens": len(items) * 4, "total_tokens": len(items) * 4},
        }

    async def list_models(
        self,
        provider: ProviderDefinition,
        secret: str | None,
    ) -> list[dict[str, Any]]:
        return [
            {"id": deployment.alias, "object": "model", "owned_by": provider.provider_id}
            for deployment in provider.deployments
        ]
