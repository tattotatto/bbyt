"""浏览记录 API 端点"""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.history import BrowseHistory
from app.models.product import Product
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.pricing import get_price_range
from app.api.deps import get_current_user

router = APIRouter()


class HistoryCreate(BaseModel):
    product_id: UUID


class HistoryItemOut(BaseModel):
    product_id: UUID
    name: str
    image: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    viewed_at: str

    model_config = {"from_attributes": True}


def _build_history_item_out(item: BrowseHistory) -> HistoryItemOut:
    """从 BrowseHistory ORM 对象构建 HistoryItemOut，拼接 Product 信息"""
    product = item.product
    image = None
    if product and product.images and len(product.images) > 0:
        image = product.images[0]
    price_min, price_max = get_price_range(product.pricing_rules) if product else (None, None)
    return HistoryItemOut(
        product_id=item.product_id,
        name=product.name if product else "",
        image=image,
        price_min=price_min,
        price_max=price_max,
        viewed_at=item.viewed_at.isoformat() if item.viewed_at else "",
    )


@router.get("", response_model=APIResponse[PaginatedResponse[HistoryItemOut]], summary="浏览记录列表")
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的浏览记录，按 viewed_at 倒序，分页返回"""
    user_id = current_user["user_id"]

    count_result = await db.execute(
        select(func.count()).select_from(BrowseHistory).where(BrowseHistory.user_id == user_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(BrowseHistory)
        .options(joinedload(BrowseHistory.product))
        .where(BrowseHistory.user_id == user_id)
        .order_by(BrowseHistory.viewed_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()

    return APIResponse.ok(data=PaginatedResponse(
        items=[_build_history_item_out(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("", response_model=APIResponse[HistoryItemOut], summary="记录/更新浏览")
async def record_history(
    req: HistoryCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录商品浏览：已存在则更新 viewed_at，不存在则新建"""
    user_id = current_user["user_id"]

    # 校验商品是否存在
    product_result = await db.execute(select(Product).where(Product.id == req.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    # 查 (user_id, product_id) 是否已有记录
    existing_result = await db.execute(
        select(BrowseHistory).where(
            BrowseHistory.user_id == user_id,
            BrowseHistory.product_id == req.product_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.viewed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(existing)
        return APIResponse.ok(data=_build_history_item_out(existing), message="已更新浏览时间")
    else:
        item = BrowseHistory(
            user_id=user_id,
            product_id=req.product_id,
            viewed_at=datetime.now(timezone.utc),
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return APIResponse.ok(data=_build_history_item_out(item), message="已记录浏览")


@router.delete("/{product_id}", response_model=APIResponse, summary="删除单条浏览记录")
async def delete_history_item(
    product_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户的某条浏览记录"""
    user_id = current_user["user_id"]

    result = await db.execute(
        select(BrowseHistory).where(
            BrowseHistory.user_id == user_id,
            BrowseHistory.product_id == product_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="浏览记录不存在")

    await db.delete(item)
    await db.flush()
    return APIResponse.ok(message="已删除")


@router.delete("", response_model=APIResponse, summary="清空浏览记录")
async def clear_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """清空当前用户的所有浏览记录"""
    await db.execute(
        delete(BrowseHistory).where(BrowseHistory.user_id == current_user["user_id"])
    )
    await db.flush()
    return APIResponse.ok(message="浏览记录已清空")
