from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep
from routex_gateway.domain.models import ProviderDefinition
from routex_gateway.storage.repositories import ProviderRepository

router = APIRouter()


@router.get("/providers")
async def list_providers(runtime: RuntimeDep, session: SessionDep):
    bundle = await runtime.control_plane_bundle(session)
    return bundle["providers"]


@router.post("/providers")
async def upsert_provider(payload: ProviderDefinition, session: SessionDep):
    provider = await ProviderRepository(session).upsert(payload)
    await session.commit()
    return provider.model_dump(mode="json")
