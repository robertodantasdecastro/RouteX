from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from routex_gateway.services.runtime import RouteXRuntime


def get_runtime(request: Request) -> RouteXRuntime:
    return request.app.state.runtime


async def get_session(request: Request) -> AsyncSession:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


def get_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str | None:
    if not authorization:
        return None
    prefix = "bearer "
    if not authorization.lower().startswith(prefix):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return authorization[len(prefix) :]


RuntimeDep = Annotated[RouteXRuntime, Depends(get_runtime)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
BearerTokenDep = Annotated[str | None, Depends(get_bearer_token)]
