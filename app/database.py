from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Callable, Optional

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

class DatabaseSessionManager:
    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    def init(self, db_uri: str) -> None:
        if not db_uri.startswith("postgresql+asyncpg://"):
            raise NotImplementedError("Only PostgreSQL with asyncpg is supported")
        self._engine = create_async_engine(
            url=db_uri,
            pool_pre_ping=True,
            # no size limit.
            pool_size=0,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._sessionmaker is None:
            raise IOError("DatabaseSessionManager is not initialized")
        async with self._sessionmaker() as session:
            try:
                yield session
            except:
                await session.rollback()
                raise

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncConnection, None]:
        if self._engine is None:
            raise IOError("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except:
                await connection.rollback()
                raise


db_manager = DatabaseSessionManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.session() as session:
        yield session


def with_db_session(func: Callable) -> Callable:
    """Decorator to inject database session into function parameters."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with db_manager.session() as db:
            return await func(*args, db, **kwargs)
    return wrapper


@asynccontextmanager
async def scoped_db_manager(
    db_uri: str,
) -> AsyncGenerator[DatabaseSessionManager, None]:
    manager = DatabaseSessionManager()
    manager.init(db_uri)

    try:
        yield manager
    finally:
        await manager.close()
