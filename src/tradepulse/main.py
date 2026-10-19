from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tradepulse.core.logger import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # События при запуске (startup)
    setup_logging(env="dev")
    logger.info("Сервис TradePulse успешно запущен", version="0.1.0")
    yield
    # События при завершении работы (shutdown)
    logger.info("Сервис TradePulse остановлен")


app = FastAPI(
    title="TradePulse API",
    lifespan=lifespan,
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    logger.debug("Вызов проверки жизнеспособности сервиса", endpoint="/health")
    return {"status": "ok"}
