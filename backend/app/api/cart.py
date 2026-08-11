"""购物车 API 端点"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.cart import CartItem
from app.models.product import Product, ProductStatus
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemOut
from app.schemas.common import APIResponse
from app.services.pricing import get_price_range
from app.api.deps import get_current_user

router = APIRouter()


def _build_cart_item_out(item: CartItem) -> CartItemOut:
    """从 CartItem ORM 对象构建 CartItemOut，拼接 Product 信息"""
    product = item.product
    image = None
    if product and product.images and len(product.images) > 0:
        image = product.images[0]
    price_min, price_max = get_price_range(product.pricing_rules) if product else (None, None)
    return CartItemOut(
        id=item.id,
        product_id=item.product_id,
        name=product.name if product else "",
        image=image,
        spec=item.spec,
        quantity=item.quantity,
        unit_price_min=price_min,
        unit_price_max=price_max,
        stock=product.stock if product else None,
        min_order_qty=product.min_order_qty if product else 0,
    )


@router.get("/", response_model=APIResponse[list[CartItemOut]], summary="我的购物车")
@router.get("", response_model=APIResponse[list[CartItemOut]], summary="我的购物车", include_in_schema=False)
async def list_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem)
        .options(joinedload(CartItem.product))
        .where(CartItem.user_id == current_user["user_id"])
    )
    items = result.scalars().all()
    return APIResponse.ok(data=[_build_cart_item_out(item) for item in items])


@router.post("/", response_model=APIResponse[CartItemOut], summary="加入购物车")
@router.post("", response_model=APIResponse[CartItemOut], summary="加入购物车", include_in_schema=False)
async def add_to_cart(
    req: CartItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 校验商品是否存在且上架
    product_result = await db.execute(
        select(Product).where(Product.id == req.product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.status != ProductStatus.ON_SALE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="商品已下架")

    # 校验库存
    if product.stock is not None and req.quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")

    # 查同 (user_id, product_id, spec) 是否已存在
    existing_result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user["user_id"],
            CartItem.product_id == req.product_id,
            CartItem.spec == req.spec,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # 累加数量
        new_qty = existing.quantity + req.quantity
        if product.stock is not None and new_qty > product.stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")
        existing.quantity = new_qty
        await db.flush()
        await db.refresh(existing)
        return APIResponse.ok(data=_build_cart_item_out(existing), message="已累加数量")
    else:
        # 新建
        item = CartItem(
            user_id=current_user["user_id"],
            product_id=req.product_id,
            spec=req.spec,
            quantity=req.quantity,
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return APIResponse.ok(data=_build_cart_item_out(item), message="已加入购物车")


@router.put("/{item_id}", response_model=APIResponse[CartItemOut], summary="修改数量")
async def update_cart_quantity(
    item_id: UUID,
    req: CartItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")

    # 权限校验：只能操作自己的购物车
    if item.user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此购物车项")

    # 库存校验
    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = product_result.scalar_one_or_none()
    if product and product.stock is not None and req.quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")

    item.quantity = req.quantity
    await db.flush()
    await db.refresh(item)
    return APIResponse.ok(data=_build_cart_item_out(item), message="数量已更新")


@router.delete("/{item_id}", response_model=APIResponse, summary="删除购物车项")
async def delete_cart_item(
    item_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")

    # 权限校验：只能操作自己的购物车
    if item.user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此购物车项")

    await db.delete(item)
    await db.flush()
    return APIResponse.ok(message="已删除")


@router.delete("/", response_model=APIResponse, summary="清空购物车")
@router.delete("", response_model=APIResponse, summary="清空购物车", include_in_schema=False)
async def clear_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(CartItem).where(CartItem.user_id == current_user["user_id"])
    )
    await db.flush()
    return APIResponse.ok(message="购物车已清空")
