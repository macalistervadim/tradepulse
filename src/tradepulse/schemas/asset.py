from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AssetType = Literal["stock", "bond", "crypto", "currency"]


class AssetCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, examples=["AAPL"])
    name: str = Field(..., min_length=1, max_length=128, examples=["Apple Inc."])
    asset_type: AssetType = Field(..., examples=["stock"])
    current_price: Decimal = Field(..., gt=0, examples=[Decimal("225.5000")])

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Тикер не может состоять только из пробелов")
        return normalized


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str
    asset_type: str
    current_price: Decimal
    created_at: datetime
