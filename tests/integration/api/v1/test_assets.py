from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tradepulse.models.asset import Asset

pytestmark = pytest.mark.integration


async def test_create_asset_success(
    async_client: AsyncClient,
    test_engine: AsyncEngine,
) -> None:
    """Успешное создание актива через API и проверка записи в таблице assets."""
    # Arrange
    payload = {
        "ticker": "aapl",  # Передаем в нижнем регистре для проверки нормализации
        "name": "Apple Inc.",
        "asset_type": "stock",
        "current_price": "225.5000",
    }

    # Act
    response = await async_client.post("/api/v1/assets", json=payload)

    # Assert: проверяем HTTP-ответ
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1  # Счетчик сброшен фикстурой clean_tables
    assert body["ticker"] == "AAPL"
    assert body["name"] == "Apple Inc."
    assert body["asset_type"] == "stock"
    assert Decimal(body["current_price"]) == Decimal("225.5000")
    assert "created_at" in body

    # Assert: проверяем фактическое состояние в PostgreSQL независимо от API
    async with AsyncSession(test_engine) as session:
        result = await session.execute(select(Asset).where(Asset.ticker == "AAPL"))
        db_asset = result.scalar_one_or_none()
        assert db_asset is not None
        assert db_asset.name == "Apple Inc."
        assert db_asset.current_price == Decimal("225.5000")


async def test_create_duplicate_asset_returns_conflict(
    async_client: AsyncClient,
    test_engine: AsyncEngine,
) -> None:
    """Попытка создать дубликат тикера возвращает 409 Conflict и не плодит записи."""
    # Arrange: создаем первый актив
    payload = {
        "ticker": "BTC",
        "name": "Bitcoin",
        "asset_type": "crypto",
        "current_price": "68500.0000",
    }
    first_response = await async_client.post("/api/v1/assets", json=payload)
    assert first_response.status_code == 201

    # Act: пытаемся создать второй актив с тем же тикером в другом регистре
    duplicate_payload = {
        "ticker": "btc",
        "name": "Bitcoin Duplicate",
        "asset_type": "crypto",
        "current_price": "69000.0000",
    }
    second_response = await async_client.post("/api/v1/assets", json=duplicate_payload)

    # Assert: проверяем код ошибки и отсутствие второй записи в БД
    assert second_response.status_code == 409
    assert "BTC" in second_response.json()["detail"]

    async with AsyncSession(test_engine) as session:
        count_result = await session.execute(select(func.count()).select_from(Asset))
        assert count_result.scalar_one() == 1


async def test_get_asset_by_ticker_success(async_client: AsyncClient) -> None:
    """Получение созданного актива по тикеру без учета регистра."""
    # Arrange
    await async_client.post(
        "/api/v1/assets",
        json={
            "ticker": "MSFT",
            "name": "Microsoft Corporation",
            "asset_type": "stock",
            "current_price": "420.1500",
        },
    )

    # Act
    response = await async_client.get("/api/v1/assets/msft")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "MSFT"
    assert data["name"] == "Microsoft Corporation"


async def test_get_nonexistent_asset_returns_not_found(
    async_client: AsyncClient,
) -> None:
    """Запрос несуществующего актива возвращает 404 Not Found."""
    # Act
    response = await async_client.get("/api/v1/assets/UNKNOWN_TICKER")

    # Assert
    assert response.status_code == 404
    assert "UNKNOWN_TICKER" in response.json()["detail"]


async def test_create_asset_invalid_json_returns_422(
    async_client: AsyncClient,
) -> None:
    """Передача отрицательной цены через HTTP отклоняется FastAPI со статусом 422."""
    # Arrange
    invalid_payload = {
        "ticker": "TSLA",
        "name": "Tesla Inc.",
        "asset_type": "stock",
        "current_price": "-100.00",
    }

    # Act
    response = await async_client.post("/api/v1/assets", json=invalid_payload)

    # Assert
    assert response.status_code == 422
