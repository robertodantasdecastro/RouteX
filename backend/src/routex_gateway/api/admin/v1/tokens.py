from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from routex_gateway.api.deps import RuntimeDep, SessionDep
from routex_gateway.domain.models import ProjectToken
from routex_gateway.storage.repositories import TokenRepository

router = APIRouter()


class TokenCreateRequest(BaseModel):
    project_id: str
    name: str
    project_config_path: str | None = None


@router.get("/projects/tokens")
async def list_tokens(session: SessionDep):
    tokens = await TokenRepository(session).list()
    return [token.model_dump(mode="json", exclude={"token_hash"}) for token in tokens]


@router.post("/projects/tokens")
async def create_token(payload: TokenCreateRequest, runtime: RuntimeDep, session: SessionDep):
    plaintext = runtime.tokens.generate_plaintext()
    token = ProjectToken(
        project_id=payload.project_id,
        name=payload.name,
        token_preview=runtime.tokens.preview(plaintext),
        token_hash=runtime.tokens.hash_token(plaintext),
        metadata={"project_config_path": payload.project_config_path}
        if payload.project_config_path
        else {},
    )
    created = await TokenRepository(session).create(token)
    await session.commit()
    return {
        "token": plaintext,
        "token_preview": created.token_preview,
        "token_id": created.token_id,
        "project_id": created.project_id,
        "name": created.name,
    }
