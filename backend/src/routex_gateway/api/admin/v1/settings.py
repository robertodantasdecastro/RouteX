from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep
from routex_gateway.domain.models import SettingsDefinition
from routex_gateway.storage.repositories import SettingsRepository

router = APIRouter()


@router.get("/settings")
async def get_settings(runtime: RuntimeDep, session: SessionDep):
    bundle = await runtime.control_plane_bundle(session)
    return bundle["settings"]


@router.post("/settings")
async def upsert_settings(payload: SettingsDefinition, session: SessionDep):
    settings = await SettingsRepository(session).upsert(payload)
    await session.commit()
    return settings.model_dump(mode="json")
