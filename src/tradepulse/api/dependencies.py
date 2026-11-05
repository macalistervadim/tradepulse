from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tradepulse.core.database import get_db_session
from tradepulse.repositories.asset import AssetRepository

# Инъекция базовой сессии
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_asset_repository(session: SessionDep) -> AssetRepository:
    """Провайдер экземпляра AssetRepository с текущей сессией запроса."""
    return AssetRepository(session=session)


# Готовый типизированный псевдоним зависимости для использования в роутерах
AssetRepoDep = Annotated[AssetRepository, Depends(get_asset_repository)]
