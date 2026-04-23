from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep
from routex_gateway.domain.models import ProfileDefinition
from routex_gateway.storage.repositories import ProfileRepository

router = APIRouter()


@router.get("/profiles")
async def list_profiles(runtime: RuntimeDep, session: SessionDep):
    bundle = await runtime.control_plane_bundle(session)
    return bundle["profiles"]


@router.post("/profiles")
async def upsert_profile(payload: ProfileDefinition, session: SessionDep):
    profile = await ProfileRepository(session).upsert(payload)
    await session.commit()
    return profile.model_dump(mode="json")
