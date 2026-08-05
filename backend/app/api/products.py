"""商品相关 API 端点"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.product import Category, Product, ProductStatus
from app.models.user import User
from app.schemas.product import (
    CategoryCreate, CategoryOut,
    ProductCreate, ProductUpdate, ProductOut, ProductListOut,
    PricingRuleUpdate, ProductPriceInfo,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.pricing import get_price, get_price_range
from app.api.deps import require_role, get_current_user
from app import redis as redis_module
import json

router = APIRouter()


# ═══════════════ 品类 API ═══════════════

@router.get("/categories", response_model=APIResponse[list[CategoryOut]], summary="品类树")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """返回树形品类结构，children 递归嵌套"""
    result = await db.execute(
        select(Category).where(Category.parent_id.is_(None)).order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    return APIResponse.ok(data=[CategoryOut.model_validate(c) for c in categories])


@router.post("/categories", response_model=APIResponse[CategoryOut], summary="创建品类（管理员）")
async def create_category(
    req: CategoryCreate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    cat = Category(**req.model_dump())
    db.add(cat)
    await db.flush()
    # Construct output manually to avoid triggering lazy-load on children
    return APIResponse.ok(data=CategoryOut(
        id=cat.id,
        parent_id=cat.parent_id,
        name=cat.name,
        icon=cat.icon,
        sort_order=cat.sort_order,
        status=cat.status,
        children=[],
    ))


# ═══════════════ 商品 API ═══════════════

@router.get("/", response_model=APIResponse[PaginatedResponse[ProductListOut]], summary="商品列表")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: UUID | None = Query(None),
    age_range: str | None = Query(None, description="适龄段筛选"),
    is_virtual: bool | None = Query(None),
    status_filter: str | None = Query("on_sale", alias="status"),
    keyword: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    # Redis 缓存（仅首页无筛选时用缓存）
    cache_key = f"products:list:{category_id}:{age_range}:{keyword}:{page}:{page_size}"
    if redis_module.redis_client:
        cached = await redis_module.redis_client.get(cache_key)
        if cached:
            return APIResponse.ok(data=json.loads(cached))

    base_query = select(Product)
    base_count = select(func.count()).select_from(Product)

    if category_id:
        base_query = base_query.where(Product.category_id == category_id)
        base_count = base_count.where(Product.category_id == category_id)
    if age_range:
        base_query = base_query.where(Product.age_range == age_range)
        base_count = base_count.where(Product.age_range == age_range)
    if is_virtual is not None:
        base_query = base_query.where(Product.is_virtual == is_virtual)
        base_count = base_count.where(Product.is_virtual == is_virtual)
    if status_filter:
        try:
            ps = ProductStatus(status_filter)
            base_query = base_query.where(Product.status == ps)
            base_count = base_count.where(Product.status == ps)
        except ValueError:
            pass  # ignore invalid status filter
    if keyword:
        base_query = base_query.where(Product.name.ilike(f"%{keyword}%"))
        base_count = base_count.where(Product.name.ilike(f"%{keyword}%"))

    total_result = await db.execute(base_count)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
    )
    products = result.scalars().all()

    items = []
    for p in products:
        price_min, price_max = get_price_range(p.pricing_rules)
        items.append(ProductListOut(
            id=p.id,
            name=p.name,
            images=p.images or [],
            age_range=p.age_range,
            safety_certifications=p.safety_certifications or [],
            is_virtual=p.is_virtual,
            stock=p.stock,
            min_order_qty=p.min_order_qty,
            status=p.status.value if hasattr(p.status, 'value') else str(p.status),
            price_min=price_min,
            price_max=price_max,
        ))

    response_data = APIResponse.ok(data=PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size
    ))

    # 查询后缓存5分钟
    if redis_module.redis_client and items:
        await redis_module.redis_client.setex(cache_key, 300, response_data.model_dump_json())

    return response_data


@router.get("/{product_id}", response_model=APIResponse[ProductOut], summary="商品详情")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return APIResponse.ok(data=ProductOut.model_validate(product))


@router.get("/{product_id}/price", response_model=APIResponse[ProductPriceInfo], summary="查询价格")
async def query_price(
    product_id: UUID,
    qty: int = Query(..., ge=1, description="采购数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """根据当前用户等级和采购数量返回匹配的单价和总价"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    # Get user level
    user_result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    level = user.level.value if hasattr(user.level, 'value') else str(user.level)
    unit_price, total_price = get_price(level, qty, product.pricing_rules)

    if unit_price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"采购数量{qty}低于最低起批量"
        )

    rules = product.pricing_rules.get(level, product.pricing_rules.get("normal", []))

    return APIResponse.ok(data=ProductPriceInfo(
        level=level,
        tiers=[{"qty": r["qty"], "price": r["price"]} for r in sorted(rules, key=lambda r: r["qty"])],
        matched_unit_price=float(unit_price),
        total_price=float(total_price),
    ))


@router.post("/", response_model=APIResponse[ProductOut], summary="创建商品（管理员）")
async def create_product(
    req: ProductCreate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    product = Product(
        **req.model_dump(),
        status=ProductStatus.OFF_SALE,
    )
    db.add(product)
    await db.flush()
    # Re-query with relationships loaded for validation
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product.id)
    )
    product_loaded = result.scalar_one()
    return APIResponse.ok(data=ProductOut.model_validate(product_loaded))


@router.put("/{product_id}", response_model=APIResponse[ProductOut], summary="编辑商品（管理员）")
async def update_product(
    product_id: UUID,
    req: ProductUpdate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.flush()
    # Re-query with relationships loaded for validation
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product_loaded = result.scalar_one()
    return APIResponse.ok(data=ProductOut.model_validate(product_loaded))


@router.put("/{product_id}/pricing", response_model=APIResponse[ProductOut], summary="设置定价规则（管理员）")
async def set_pricing(
    product_id: UUID,
    req: PricingRuleUpdate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    product.pricing_rules = req.pricing_rules
    await db.flush()
    # Re-query with relationships loaded for validation
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product_loaded = result.scalar_one()
    return APIResponse.ok(data=ProductOut.model_validate(product_loaded))


@router.put("/{product_id}/status", response_model=APIResponse[ProductOut], summary="上下架（管理员）")
async def toggle_status(
    product_id: UUID,
    status_action: str = Query(..., pattern="^(on_sale|off_sale)$"),
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    product.status = ProductStatus(status_action)
    await db.flush()
    # Re-query with relationships loaded for validation
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product_loaded = result.scalar_one()
    return APIResponse.ok(data=ProductOut.model_validate(product_loaded))
