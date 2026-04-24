from __future__ import annotations

from fastapi import APIRouter, Query

from routex_gateway.api.deps import RuntimeDep, SessionDep
from routex_gateway.domain.models import RuleDefinition
from routex_gateway.storage.repositories import RuleRepository

router = APIRouter()


@router.get("/rules")
async def list_rules(runtime: RuntimeDep, session: SessionDep):
    bundle = await runtime.control_plane_bundle(session)
    return bundle["rules"]


@router.post("/rules")
async def upsert_rule(payload: RuleDefinition, session: SessionDep):
    rule = await RuleRepository(session).upsert(payload)
    await session.commit()
    return rule.model_dump(mode="json")


@router.get("/routing/preview")
async def preview_route(
    runtime: RuntimeDep,
    session: SessionDep,
    model_alias: str = Query(...),
    profile_id: str | None = Query(None),
    project_id: str | None = Query(None),
    provider_hint: str | None = Query(None),
    deployment_hint: str | None = Query(None),
):
    return await runtime.route_preview(
        session,
        model_alias=model_alias,
        profile_id=profile_id,
        project_id=project_id,
        provider_hint=provider_hint,
        deployment_hint=deployment_hint,
    )
