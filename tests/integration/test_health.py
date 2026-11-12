import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_healthcheck_returns_connected_db(async_client: AsyncClient) -> None:
    """Проверка готовности сервиса и активного соединения с тестовой PostgreSQL."""
    # Act
    response = await async_client.get("/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "PostgreSQL 17" in data["postgres_version"]
