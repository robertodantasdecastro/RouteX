from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep

router = APIRouter()


@router.get("/health")
async def health(runtime: RuntimeDep, session: SessionDep):
    response = await runtime.health_payload(session)
    return response.model_dump(mode="json")
