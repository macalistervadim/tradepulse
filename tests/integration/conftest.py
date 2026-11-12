from collections.abc import AsyncGenerator
import os
from pathlib import Path

from dotenv import load_dotenv
import pytest
from httpx import ASGITransport, AsyncClient

# 1. Загружаем тестовые переменные окружения ДО импорта приложения и настроек
env_test_path = Path(__file__).resolve().parent.parent / ".env.test"
if env_test_path.exists():
    load_dotenv(dotenv_path=env_test_path, override=True)
else:
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("POSTGRES_PORT", "5434")
    os.environ.setdefault("POSTGRES_DB", "tradepulse_test_db")

# Импортируем приложение только после инициализации тестового окружения
from tradepulse.main import app  # noqa: E402


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный HTTP-клиент для прямого тестирования ASGI-приложения."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client
