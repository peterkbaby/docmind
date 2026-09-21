
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import FastAPI
from core.config import settings



class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db(app: FastAPI) -> None:
    app.state.engine = engine
    app.state.session_local = SessionLocal

async def close_db(app: FastAPI) -> None:
    await engine.dispose()

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


    