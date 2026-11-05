from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradepulse.models.asset import Asset
from tradepulse.repositories.base import BaseDAO


class AssetRepository(BaseDAO[Asset]):
    """Специализированный репозиторий для финансовых активов."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Asset, session=session)

    async def get_by_ticker(self, ticker: str) -> Asset | None:
        """Поиск актива по биржевому тикеру без учета регистра."""
        query = select(self.model).where(
            func.upper(self.model.ticker) == ticker.strip().upper()
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
