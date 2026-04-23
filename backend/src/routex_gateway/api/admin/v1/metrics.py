from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import RuntimeDep, SessionDep

router = APIRouter()


@router.get("/metrics")
async def get_metrics(runtime: RuntimeDep, session: SessionDep):
    return await runtime.metrics.snapshot(session)
