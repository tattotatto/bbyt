"""用户管理 API（管理员用）"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserStatus, RetailerLevel, RetailerProfile
from app.schemas.user import UserOut, UserListOut, ReviewRetailerRequest, RetailerProfileUpdate
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.deps import get_current_user, get_current_admin, require_role

router = APIRouter()


@router.get("/me", response_model=APIResponse[UserOut], summary="获取当前用户信息")
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.retailer_profile))
        .where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return APIResponse.ok(data=UserOut.model_validate(user))


@router.put("/me/profile", response_model=APIResponse[UserOut], summary="更新企业资料（零售商）")
async def update_retailer_profile(
    req: RetailerProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """部分更新当前零售商的企业资料；未传字段保持不变。无 profile 时自动创建。"""
    if current_user["role"] != "retailer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅零售商可更新企业资料")

    result = await db.execute(
        select(User)
        .options(selectinload(User.retailer_profile))
        .where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 若无 profile 则新建（必填字段给默认空字符串，后续由 update_data 覆盖传入字段）
    if not user.retailer_profile:
        user.retailer_profile = RetailerProfile(
            user_id=user.id,
            company_name="",
            business_license="",
            contact_person="",
        )
        db.add(user.retailer_profile)

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user.retailer_profile, field, value)

    await db.flush()
    return APIResponse.ok(data=UserOut.model_validate(user))


@router.get("/", response_model=APIResponse[PaginatedResponse[UserListOut]], summary="用户列表（管理员）")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = Query(None, description="按角色筛选"),
    status: str | None = Query(None, description="按状态筛选"),
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    # Build query with eager-loaded retailer_profile
    query = select(User).options(selectinload(User.retailer_profile))

    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)

    # Count total
    count_query = select(func.count()).select_from(User)
    if role:
        count_query = count_query.where(User.role == role)
    if status:
        count_query = count_query.where(User.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(User.created_at.desc()).offset(offset).limit(page_size))
    users = result.scalars().all()

    # Build output with company_name from retailer profile
    items = []
    for user in users:
        company_name = None
        contact_person = None
        if user.retailer_profile:
            company_name = user.retailer_profile.company_name
            contact_person = user.retailer_profile.contact_person
        items.append(UserListOut(
            id=user.id,
            phone=user.phone,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            level=user.level.value if hasattr(user.level, 'value') else user.level,
            status=user.status.value if hasattr(user.status, 'value') else user.status,
            company_name=company_name,
            contact_person=contact_person,
            created_at=user.created_at,
        ))

    return APIResponse.ok(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("/review", response_model=APIResponse[UserOut], summary="审核零售商（管理员）")
async def review_retailer(
    req: ReviewRetailerRequest,
    _admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.retailer_profile))
        .where(User.id == req.user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if req.action == "approve":
        user.status = UserStatus.ACTIVE
        if req.level:
            user.level = RetailerLevel(req.level)
        if req.credit_limit is not None:
            user.credit_limit = req.credit_limit
    elif req.action == "reject":
        user.status = UserStatus.FROZEN
        # Could store reject_reason in a log table; for now just set status

    await db.flush()
    return APIResponse.ok(data=UserOut.model_validate(user), message="审核完成")
