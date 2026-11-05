from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssetType = Literal["stock", "bond", "crypto", "currency"]


class AssetCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, examples=["AAPL"])
    name: str = Field(..., min_length=1, max_length=128, examples=["Apple Inc."])
    asset_type: AssetType = Field(..., examples=["stock"])
    current_price: Decimal = Field(..., gt=0, examples=[ Decimal("225.5000") ])


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str
    asset_type: str
    current_price: Decimal
    created_at: datetime
