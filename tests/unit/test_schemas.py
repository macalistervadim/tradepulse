from decimal import Decimal

import pytest
from pydantic import ValidationError

from tradepulse.schemas.asset import AssetCreate

# Применяем маркер unit ко всем тестам в этом модуле
pytestmark = pytest.mark.unit


def test_asset_create_valid_payload() -> None:
    """Проверка успешной валидации корректных данных финансового актива."""
    # Arrange
    raw_data = {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "asset_type": "stock",
        "current_price": "135.7500",
    }

    # Act
    schema = AssetCreate(**raw_data)  # type: ignore[arg-type]

    # Assert
    assert schema.ticker == "NVDA"
    assert schema.name == "NVIDIA Corporation"
    assert schema.asset_type == "stock"
    assert schema.current_price == Decimal("135.7500")


@pytest.mark.parametrize(
    ("invalid_field", "invalid_value"),
    [
        ("ticker", ""),  # Пустой тикер запрещен (min_length=1)
        ("ticker", "A" * 17),  # Превышение длины тикера (max_length=16)
        ("name", ""),  # Пустое наименование запрещено
        ("asset_type", "real_estate"),  # Недопустимый тип актива (не входит в Literal)
        ("current_price", 0),  # Нулевая цена запрещена (gt=0)
        ("current_price", -15.5),  # Отрицательная цена запрещена (gt=0)
    ],
)
def test_asset_create_validation_errors(
    invalid_field: str,
    invalid_value: str | float,
) -> None:
    """Параметризованная проверка отклонения некорректных полей схемы AssetCreate."""
    # Arrange
    payload: dict[str, object] = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "stock",
        "current_price": Decimal("225.50"),
    }
    payload[invalid_field] = invalid_value

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        AssetCreate(**payload)  # type: ignore[arg-type]

    # Убеждаемся, что ошибка валидации возникла именно в проверяемом поле
    errors = exc_info.value.errors()
    assert any(err["loc"] == (invalid_field,) for err in errors)
