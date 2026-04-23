from __future__ import annotations

from fastapi import APIRouter

from routex_gateway.api.deps import SessionDep
from routex_gateway.storage.repositories import RequestLogRepository

router = APIRouter()


@router.get("/requests")
async def list_requests(session: SessionDep):
    records = await RequestLogRepository(session).list_recent()
    return [record.model_dump(mode="json") for record in records]
