"""设计案例 API 端点"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.case import DesignCase
from app.schemas.case import CaseCreate, CaseUpdate, CaseOut, CaseListOut
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.deps import require_role

router = APIRouter()


@router.get("/featured", response_model=APIResponse[list[CaseListOut]], summary="精选案例（首页展示）")
async def list_featured_cases(
    limit: int = Query(6, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """返回精选案例，按 sort_order 降序，用于首页展示"""
    result = await db.execute(
        select(DesignCase)
        .where(DesignCase.is_featured == True, DesignCase.status == "published")
        .order_by(DesignCase.sort_order.desc())
        .limit(limit)
    )
    cases = result.scalars().all()
    return APIResponse.ok(data=[CaseListOut.model_validate(c) for c in cases])


@router.get("/", response_model=APIResponse[PaginatedResponse[CaseListOut]], summary="案例列表")
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    style: str | None = Query(None, description="按风格筛选: ins风/自然原木/卡通童趣"),
    area: str | None = Query(None, description="按面积筛选: 50-100㎡/100-200㎡/200㎡+"),
    category_tag: str | None = Query(None, description="按类型筛选: 婴童游泳馆/母婴生活馆/儿童乐园"),
    db: AsyncSession = Depends(get_db),
):
    query = select(DesignCase).where(DesignCase.status == "published")
    count_query = select(func.count()).select_from(DesignCase).where(DesignCase.status == "published")

    # JSON array contains filter - use PostgreSQL @> or simple LIKE for SQLite compat
    if style:
        query = query.where(DesignCase.style_tags.contains([style]))
        count_query = count_query.where(DesignCase.style_tags.contains([style]))
    if area:
        query = query.where(DesignCase.store_area_range == area)
        count_query = count_query.where(DesignCase.store_area_range == area)
    if category_tag:
        query = query.where(DesignCase.category_tags.contains([category_tag]))
        count_query = count_query.where(DesignCase.category_tags.contains([category_tag]))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(DesignCase.sort_order.desc(), DesignCase.created_at.desc())
        .offset(offset).limit(page_size)
    )
    cases = result.scalars().all()

    return APIResponse.ok(data=PaginatedResponse(
        items=[CaseListOut.model_validate(c) for c in cases],
        total=total, page=page, page_size=page_size
    ))


@router.get("/tags", response_model=APIResponse[dict], summary="获取所有可用标签")
async def list_tags(db: AsyncSession = Depends(get_db)):
    """返回系统中所有已使用的 category_tags 和 style_tags（用于筛选器）"""
    result = await db.execute(
        select(DesignCase).where(DesignCase.status == "published")
    )
    cases = result.scalars().all()

    category_tags = set()
    style_tags = set()
    area_ranges = set()
    for c in cases:
        for t in (c.category_tags or []):
            category_tags.add(t)
        for t in (c.style_tags or []):
            style_tags.add(t)
        if c.store_area_range:
            area_ranges.add(c.store_area_range)

    return APIResponse.ok(data={
        "category_tags": sorted(category_tags),
        "style_tags": sorted(style_tags),
        "area_ranges": sorted(area_ranges),
    })


@router.get("/{case_id}", response_model=APIResponse[CaseOut], summary="案例详情")
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DesignCase).where(DesignCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案例不存在")
    return APIResponse.ok(data=CaseOut.model_validate(case))


@router.post("/", response_model=APIResponse[CaseOut], summary="创建案例（管理员）")
async def create_case(
    req: CaseCreate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    case = DesignCase(**req.model_dump())
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return APIResponse.ok(data=CaseOut.model_validate(case))


@router.put("/{case_id}", response_model=APIResponse[CaseOut], summary="编辑案例（管理员）")
async def update_case(
    case_id: UUID,
    req: CaseUpdate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DesignCase).where(DesignCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案例不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)

    await db.flush()
    await db.refresh(case)
    return APIResponse.ok(data=CaseOut.model_validate(case))


@router.delete("/{case_id}", response_model=APIResponse, summary="删除案例（管理员）")
async def delete_case(
    case_id: UUID,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DesignCase).where(DesignCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="案例不存在")
    await db.delete(case)
    await db.flush()
    return APIResponse.ok(message="案例已删除")
