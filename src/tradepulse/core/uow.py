from abc import ABC, abstractmethod
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tradepulse.core.database import async_session_maker
from tradepulse.repositories.asset import AssetRepository


class IUnitOfWork(ABC):
    """Абстрактный интерфейс паттерна Unit of Work."""

    assets: AssetRepository

    async def __aenter__(self) -> "IUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        """Фиксация изменений текущей транзакции."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Откат всех незафиксированных изменений текущей транзакции."""
        raise NotImplementedError


class UnitOfWork(IUnitOfWork):
    """Асинхронная реализация Unit of Work на базе SQLAlchemy AsyncSession."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = async_session_maker,
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        # 1. Открываем изолированную сессию при входе в контекст
        self._session = self._session_factory()

        # 2. Инициализируем репозитории с одной общей сессией
        self.assets = AssetRepository(session=self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        # Гарантируем закрытие сессии и возврат сокета в пул при любом исходе
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        """Явная фиксация изменений транзакции."""
        if self._session is not None:
            await self._session.commit()

    async def rollback(self) -> None:
        """Откат незафиксированных изменений транзакции."""
        if self._session is not None:
            await self._session.rollback()
