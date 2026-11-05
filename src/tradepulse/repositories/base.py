from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tradepulse.core.database import Base


class BaseDAO[ModelType: Base]:
    """Базовый класс слоя доступа к данным (Data Access Object / Repository)."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, obj_id: Any) -> ModelType | None:
        """Получение одной записи по первичному ключу."""
        return await self.session.get(self.model, obj_id)

    async def find_one_or_none(self, **filter_by: Any) -> ModelType | None:
        """Поиск единственной записи по заданным критериям фильтрации."""
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filter_by: Any,
    ) -> Sequence[ModelType]:
        """Выборка списка сущностей с поддержкой пагинации и фильтрации."""
        query = select(self.model).filter_by(**filter_by).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add(self, **data: Any) -> ModelType:
        """Создание нового объекта в рамках текущей сессии."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, obj_id: Any, **data: Any) -> ModelType | None:
        """Атомарное обновление полей записи."""
        query = (
            update(self.model)
            .where(self.model.id == obj_id)  # type: ignore[attr-defined]
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, obj_id: Any) -> bool:
        """Удаление записи по первичному ключу."""
        query = (
            delete(self.model)
            .where(self.model.id == obj_id)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(query)
        return bool(result.rowcount and result.rowcount > 0)
