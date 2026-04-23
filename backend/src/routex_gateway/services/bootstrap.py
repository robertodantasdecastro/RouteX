from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from routex_gateway.storage.db import Base


async def initialize_database(session_factory: async_sessionmaker[AsyncSession], engine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        await _seed_defaults(session)
        await session.commit()


async def _seed_defaults(session: AsyncSession) -> None:
    # SQLite persists only local overrides and audit/history rows.
    # Versioned manifests under configs/ must remain the primary source of truth.
    await session.flush()
