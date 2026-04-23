from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from routex_gateway.domain.models import (
    ChatCompletionsRequest,
    DeploymentDefinition,
    EmbeddingsRequest,
    ProviderDefinition,
    ResponsesRequest,
)


class AdapterExecutionError(RuntimeError):
    def __init__(self, message: str, status_code: int = 500, error_class: str = "adapter_error"):
        super().__init__(message)
        self.status_code = status_code
        self.error_class = error_class


class ProviderAdapter(ABC):
    @abstractmethod
    def supports(self, provider: ProviderDefinition) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def chat_completions(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ChatCompletionsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def responses(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: ResponsesRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def embeddings(
        self,
        provider: ProviderDefinition,
        deployment: DeploymentDefinition,
        request: EmbeddingsRequest,
        secret: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def list_models(
        self,
        provider: ProviderDefinition,
        secret: str | None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
