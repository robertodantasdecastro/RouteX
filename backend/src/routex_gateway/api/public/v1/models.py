from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep

router = APIRouter()


@router.get("/models")
async def list_models(runtime: RuntimeDep, session: SessionDep):
    aliases = await runtime.catalog.list_model_aliases(session)
    return {
        "object": "list",
        "data": [
            {
                "id": alias.alias,
                "object": "model",
                "owned_by": alias.preferred_provider_id or "routex",
                "capabilities": alias.capabilities.model_dump(mode="json"),
                "deployments": [
                    deployment.model_dump(mode="json") for deployment in alias.deployments
                ],
            }
            for alias in aliases
        ],
    }
