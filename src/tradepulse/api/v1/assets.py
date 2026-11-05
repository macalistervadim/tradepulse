from fastapi import APIRouter, HTTPException, status

from tradepulse.api.dependencies import UOWDep
from tradepulse.schemas.asset import AssetCreate, AssetResponse

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового актива",
)
async def create_asset(
    payload: AssetCreate,
    uow: UOWDep,
) -> AssetResponse:
    # 1. Проверяем бизнес-правило уникальности тикера
    existing_asset = await uow.assets.get_by_ticker(payload.ticker)
    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Актив с тикером '{payload.ticker}' уже зарегистрирован в системе",
        )

    # 2. Создаем сущность через репозиторий в рамках транзакции UoW
    asset = await uow.assets.add(
        ticker=payload.ticker.upper(),
        name=payload.name,
        asset_type=payload.asset_type,
        current_price=payload.current_price,
    )

    # Фиксация произойдет автоматически при успешном выходе из генератора зависимости get_uow
    return AssetResponse.model_validate(asset)


@router.get(
    "/{ticker}",
    response_model=AssetResponse,
    summary="Получение актива по тикеру",
)
async def get_asset(
    ticker: str,
    uow: UOWDep,
) -> AssetResponse:
    asset = await uow.assets.get_by_ticker(ticker)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Актив с тикером '{ticker}' не найден",
        )
    return AssetResponse.model_validate(asset)
