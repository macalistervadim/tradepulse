from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from tradepulse.core.config import settings

# 1. Создание асинхронного движка с настройкой пула
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Автоматическая проверка живого сокета перед выдачей из пула
)

# 2. Фабрика создания асинхронных сессий
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Предотвращает перезагрузку атрибутов после commit
    autoflush=False,
)

# 3. Базовый декларативный класс для будущих ORM-моделей
class Base(DeclarativeBase):
    pass

# 4. FastAPI Dependency для безопасной выдачи сессий в эндпоинты
async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Генератор сессии БД: гарантирует возврат коннекта в пул и откат при ошибке."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
