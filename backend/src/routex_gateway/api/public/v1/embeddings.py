from __future__ import annotations

from fastapi import APIRouter, HTTPException

from routex_gateway.api.deps import BearerTokenDep, RuntimeDep, SessionDep
from routex_gateway.domain.models import EmbeddingsRequest
from routex_gateway.providers.base import AdapterExecutionError
from routex_gateway.services.routing import RoutingError

router = APIRouter()


@router.post("/embeddings")
async def embeddings(
    payload: EmbeddingsRequest,
    runtime: RuntimeDep,
    session: SessionDep,
    bearer_token: BearerTokenDep,
):
    try:
        return await runtime.execute_embeddings(session, payload, bearer_token)
    except AdapterExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.args[0]) from exc
    except RoutingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
