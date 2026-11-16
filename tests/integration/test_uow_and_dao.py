from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from tradepulse.core.uow import UnitOfWork

pytestmark = pytest.mark.integration


def _make_uow(test_engine: AsyncEngine) -> UnitOfWork:
    """Фабрика UnitOfWork, привязанная к тестовому движку."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return UnitOfWork(session_factory=session_factory)


async def test_base_dao_crud_lifecycle(test_engine: AsyncEngine) -> None:
    """Проверка полного цикла CRUD в BaseDAO: add, get_by_id, find_one_or_none, find_all, update, delete."""
    uow = _make_uow(test_engine)

    # 1. Create (add)
    async with uow:
        created = await uow.assets.add(
            ticker="GOOGL",
            name="Alphabet Inc.",
            asset_type="stock",
            current_price=Decimal("175.2000"),
        )
        asset_id = created.id

    # 2. Read (get_by_id, find_one_or_none, find_all)
    async with uow:
        fetched = await uow.assets.get_by_id(asset_id)
        assert fetched is not None
        assert fetched.ticker == "GOOGL"

        found_one = await uow.assets.find_one_or_none(ticker="GOOGL")
        assert found_one is not None
        assert found_one.id == asset_id

        all_assets = await uow.assets.find_all(skip=0, limit=10)
        assert len(all_assets) == 1

    # 3. Update
    async with uow:
        updated = await uow.assets.update(
            asset_id,
            current_price=Decimal("180.5000"),
        )
        assert updated is not None
        assert updated.current_price == Decimal("180.5000")

    # 4. Delete
    async with uow:
        deleted = await uow.assets.delete(asset_id)
        assert deleted is True

        # Повторное удаление несуществующей записи возвращает False
        deleted_again = await uow.assets.delete(asset_id)
        assert deleted_again is False


async def test_uow_rollback_on_unhandled_exception(
    test_engine: AsyncEngine,
) -> None:
    """Необработанное исключение внутри блока async with uow откатывает транзакцию."""
    uow = _make_uow(test_engine)

    with pytest.raises(RuntimeError, match="Simulated failure"):
        async with uow:
            await uow.assets.add(
                ticker="AMZN",
                name="Amazon.com Inc.",
                asset_type="stock",
                current_price=Decimal("190.0000"),
            )
            # Имитируем внезапный сбой до выхода из контекста
            raise RuntimeError("Simulated failure")

    # Проверяем в новой сессии, что запись AMZN не попала в базу данных
    async with uow:
        asset = await uow.assets.get_by_ticker("AMZN")
        assert asset is None
