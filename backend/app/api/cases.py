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
@router.get("", response_model=APIResponse[PaginatedResponse[CaseListOut]], summary="案例列表", include_in_schema=False)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    style: str | None = Query(None, description="按风格筛选: ins风/自然原木/卡通童趣"),
    area: str | None = Query(None, description="按面积筛选: 50-100㎡/100-200㎡/200㎡+"),
    category_tag: str | None = Query(None, description="按类型筛选: 婴童游泳馆/母婴生活馆/儿童乐园"),
    db: AsyncSession = Depends(get_db),
):
    base_filters = [DesignCase.status == "published"]
    if area:
        base_filters.append(DesignCase.store_area_range == area)

    ordered = (
        select(DesignCase)
        .where(*base_filters)
        .order_by(DesignCase.sort_order.desc(), DesignCase.created_at.desc())
    )

    if style or category_tag:
        # 标签列是通用 JSON（非 JSONB）：PG 上没有 @>，SQLite 上也没有统一的包含运算符。
        # JSON.contains([x]) 会退化成子串 LIKE，模式是序列化后的 ["x"]，只对「恰好是单元素
        # 数组」的记录成立——多标签记录永远筛不到。而改写成 cast 成文本再 LIKE 也不行：
        # 通用 JSON 用 json.dumps 默认参数序列化，非 ASCII 会被转义成 \uXXXX 落库，
        # 且 PG 的 LIKE 把反斜杠当默认转义符，两个库要分别转义，本地根本验不了。
        # 所以在应用层过滤：两个库上语义完全一致，本地 SQLite 测试即代表线上行为。
        # 代价是带标签筛选时整表取回内存——设计案例是策展型图集（几十条量级），
        # 且本文件 list_tags 已经是同样整体加载的写法，量级上站得住。
        result = await db.execute(ordered)
        cases = [
            c
            for c in result.scalars().all()
            if (not style or style in (c.style_tags or []))
            and (not category_tag or category_tag in (c.category_tags or []))
        ]
        total = len(cases)
        cases = cases[(page - 1) * page_size: page * page_size]
    else:
        count_query = select(func.count()).select_from(DesignCase).where(*base_filters)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await db.execute(ordered.offset(offset).limit(page_size))
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
@router.post("", response_model=APIResponse[CaseOut], summary="创建案例（管理员）", include_in_schema=False)
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
