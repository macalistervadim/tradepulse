import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

# 1. Загружаем тестовые переменные окружения ДО импорта приложения и настроек
ROOT_DIR = Path(__file__).resolve().parent.parent
env_test_path = ROOT_DIR / ".env.test"

if env_test_path.exists():
    load_dotenv(dotenv_path=env_test_path, override=True)
else:
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("POSTGRES_USER", "tradepulse_test")
    os.environ.setdefault("POSTGRES_PASSWORD", "tradepulse_test_password")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5434")
    os.environ.setdefault("POSTGRES_DB", "tradepulse_test_db")

# Импортируем модули приложения строго после загрузки .env.test
from tradepulse.core.config import settings  # noqa: E402
from tradepulse.core.database import Base  # noqa: E402
from tradepulse.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """Однократно применяет все миграции Alembic к тестовой БД перед стартом тестов."""
    alembic_cfg = Config(str(ROOT_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "migrations"))
    # Передаем URL тестовой базы данных в конфигурацию Alembic
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    # Применяем миграции до актуальной ревизии head
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """Создает изолированный движок для служебных операций очистки БД в тестах."""
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(
    apply_migrations: None,
    test_engine: AsyncEngine,
) -> AsyncGenerator[None]:
    """Гарантирует пустое состояние всех таблиц перед каждым тестом."""
    yield

    # Собираем имена всех зарегистрированных в метаданных таблиц
    table_names = [table.name for table in Base.metadata.sorted_tables]
    if not table_names:
        return

    tables_str = ", ".join(f'"{name}"' for name in table_names)
    async with test_engine.begin() as conn:
        # Быстрая очистка с обнулением счетчиков автоинкремента (ID снова начинаются с 1)
        await conn.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Асинхронный HTTP-клиент для прямого тестирования ASGI-приложения."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client
