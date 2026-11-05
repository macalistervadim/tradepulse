from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tradepulse.api.v1.assets import router as assets_router
from tradepulse.core.database import engine, get_db_session
from tradepulse.core.logger import logger, setup_logging

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(env="dev")
    logger.info("Инициализация сервиса TradePulse", version="0.1.0")

    # Проверка доступности базы данных при старте
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Успешное подключение к пулу PostgreSQL")
    except Exception as exc:
        logger.error("Не удалось подключиться к PostgreSQL", error=str(exc))
        raise

    yield

    # Корректное закрытие соединений при остановке
    await engine.dispose()
    logger.info("Пул соединений с PostgreSQL закрыт")

app = FastAPI(
    title="TradePulse API",
    lifespan=lifespan,
)
app.include_router(assets_router, prefix="/api/v1")

@app.get("/health")
async def healthcheck(
        db: DBSessionDep,
) -> dict[str, str]:
    # Выполняем проверочный неблокирующий SQL-запрос через выданную сессию
    result = await db.execute(text("SELECT version();"))
    db_version = result.scalar() or "unknown"

    logger.debug("Проверка здоровья сервиса и БД пройдена")
    return {
        "status": "ok",
        "database": "connected",
        "postgres_version": str(db_version),
    }
