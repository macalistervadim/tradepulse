import asyncio
import os
import sys
from logging.config import fileConfig

# 1. Обеспечиваем видимость пакета tradepulse при компоновке src-layout
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ВАЖНО: импортируем модуль моделей, чтобы они зарегистрировались в Base.metadata
import tradepulse.models  # noqa: F401

# 2. Импортируем конфигурацию приложения и метаданные моделей
from tradepulse.core.config import settings
from tradepulse.core.database import Base

config = context.config

# Настройка логирования из alembic.ini, если конфиг передан
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Указываем метаданные для механизма автогенерации
target_metadata = Base.metadata

# 4. Переопределяем URL подключения из наших pydantic-настроек
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Выполнение миграций в 'offline'-режиме (генерация SQL без живого коннекта)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Отслеживание изменений типов колонок
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Синхронная функция выполнения миграций внутри контекста адаптера run_sync."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Асинхронная инициализация движка и мост через run_sync для asyncpg."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Выполнение миграций в 'online'-режиме с живым подключением к базе данных."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
