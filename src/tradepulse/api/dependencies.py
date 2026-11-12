from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tradepulse.core.database import get_db_session
from tradepulse.core.uow import IUnitOfWork, UnitOfWork
from tradepulse.repositories.asset import AssetRepository

# Инъекция базовой сессии
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_asset_repository(session: SessionDep) -> AssetRepository:
    """Провайдер экземпляра AssetRepository с текущей сессией запроса."""
    return AssetRepository(session=session)


async def get_uow() -> AsyncGenerator[IUnitOfWork]:
    """Генератор единицы работы (Unit of Work) на время обработки запроса."""
    uow = UnitOfWork()
    async with uow:
        yield uow


# Типизированный псевдоним зависимости для чистой инъекции в контроллеры и сервисы
UOWDep = Annotated[IUnitOfWork, Depends(get_uow)]


# Готовый типизированный псевдоним зависимости для использования в роутерах
AssetRepoDep = Annotated[AssetRepository, Depends(get_asset_repository)]
