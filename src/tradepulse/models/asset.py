from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from tradepulse.core.database import Base

AssetType = Literal["stock", "bond", "crypto", "currency"]


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # В финтех-системах стоимость фиксируется строго через Decimal/Numeric, а не Float
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Asset ticker='{self.ticker}' price='{self.current_price}'>"
