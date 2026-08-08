"""收藏 API 端点"""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.favorite import Favorite
from app.models.product import Product
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.pricing import get_price_range
from app.api.deps import get_current_user

router = APIRouter()


class FavoriteCreate(BaseModel):
    product_id: UUID


class FavoriteItemOut(BaseModel):
    product_id: UUID
    name: str
    image: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    created_at: str

    model_config = {"from_attributes": True}


def _build_favorite_item_out(
    item: Favorite, product: Product | None = None
) -> FavoriteItemOut:
    """从 Favorite ORM 对象构建 FavoriteItemOut，拼接 Product 信息。
    若传入 product 则直接使用，避免再触发 lazy-load。"""
    product = product or item.product
    image = None
    if product and product.images and len(product.images) > 0:
        image = product.images[0]
    price_min, price_max = get_price_range(product.pricing_rules) if product else (None, None)
    return FavoriteItemOut(
        product_id=item.product_id,
        name=product.name if product else "",
        image=image,
        price_min=price_min,
        price_max=price_max,
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.get("", response_model=APIResponse[PaginatedResponse[FavoriteItemOut]], summary="收藏列表")
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏列表，按 created_at 倒序，分页返回"""
    user_id = current_user["user_id"]

    count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Favorite)
        .options(joinedload(Favorite.product))
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()

    return APIResponse.ok(data=PaginatedResponse(
        items=[_build_favorite_item_out(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("", response_model=APIResponse, summary="添加收藏")
async def add_favorite(
    req: FavoriteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加商品收藏，幂等：已存在或并发冲突（IntegrityError）静默成功"""
    user_id = current_user["user_id"]

    # 校验商品是否存在
    product_result = await db.execute(select(Product).where(Product.id == req.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    # 先查是否存在
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.product_id == req.product_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return APIResponse.ok(message="已收藏")

    # 不存在则新建；并发冲突时 IntegrityError 静默成功
    try:
        favorite = Favorite(
            user_id=user_id,
            product_id=req.product_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(favorite)
        await db.flush()
        return APIResponse.ok(message="收藏成功")
    except IntegrityError:
        await db.rollback()
        return APIResponse.ok(message="已收藏")


@router.delete("/{product_id}", response_model=APIResponse, summary="取消收藏")
async def remove_favorite(
    product_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏某个商品"""
    user_id = current_user["user_id"]

    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.product_id == product_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏不存在")

    await db.delete(item)
    await db.flush()
    return APIResponse.ok(message="已取消收藏")


@router.get("/{product_id}", response_model=APIResponse[dict], summary="检查是否已收藏")
async def check_favorite(
    product_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查当前用户是否已收藏某个商品，返回 {"is_favorited": bool}"""
    user_id = current_user["user_id"]

    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.product_id == product_id,
        )
    )
    existing = result.scalar_one_or_none()
    return APIResponse.ok(data={"is_favorited": existing is not None})
