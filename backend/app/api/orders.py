"""订单 API 端点"""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from app.database import get_db
from app.models.order import Order, OrderStatus, PaymentStatus, PaymentMethod
from app.models.user import User, UserRole, UserStatus
from app.schemas.order import (
    OrderCreate, OrderOut, OrderListOut, OrderStatusUpdate,
    AssignDesignerRequest, PaymentSubmit,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.order_service import create_order
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.post("/", response_model=APIResponse[OrderOut], summary="创建订单")
async def place_order(
    req: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建订单：校验库存、匹配价格、生成快照"""
    # 审核门禁：非 ACTIVE 且非 admin/operator → 拒绝下单
    if current_user["role"] not in ("admin", "operator"):
        result = await db.execute(
            select(User.status).where(User.id == current_user["user_id"])
        )
        user_status = result.scalar_one_or_none()
        if user_status is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user_status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号审核中，暂不能下单")

    try:
        items_dicts = [item.model_dump() for item in req.items]
        order = await create_order(
            db=db,
            retailer_id=current_user["user_id"],
            items=items_dicts,
            payment_method=req.payment_method,
            remark=req.remark,
            receiver_name=req.receiver_name,
            receiver_phone=req.receiver_phone,
            receiver_address=req.receiver_address,
            store_design_detail=req.store_design_detail,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await db.flush()
    await db.refresh(order)
    return APIResponse.ok(data=OrderOut.model_validate(order), message="订单创建成功")


@router.get("/", response_model=APIResponse[PaginatedResponse[OrderListOut]], summary="我的订单列表")
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status", description="按状态筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order).where(Order.retailer_id == current_user["user_id"])
    count_query = select(func.count()).select_from(Order).where(Order.retailer_id == current_user["user_id"])

    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Order.created_at.desc()).offset(offset).limit(page_size))
    orders = result.scalars().all()

    return APIResponse.ok(data=PaginatedResponse(
        items=[OrderListOut.model_validate(o) for o in orders],
        total=total, page=page, page_size=page_size
    ))


@router.get("/admin", response_model=APIResponse[PaginatedResponse[OrderListOut]], summary="所有订单（管理员）")
async def list_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order)
    count_query = select(func.count()).select_from(Order)

    if status_filter:
        query = query.where(Order.status == status_filter)
        count_query = count_query.where(Order.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Order.created_at.desc()).offset(offset).limit(page_size))
    orders = result.scalars().all()

    return APIResponse.ok(data=PaginatedResponse(
        items=[OrderListOut.model_validate(o) for o in orders],
        total=total, page=page, page_size=page_size
    ))


@router.get("/{order_id}", response_model=APIResponse[OrderOut], summary="订单详情")
async def get_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    # 管理员可查看所有订单
    if current_user["role"] not in ("admin", "operator") and order.retailer_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此订单")

    return APIResponse.ok(data=OrderOut.model_validate(order))


@router.put("/{order_id}/status", response_model=APIResponse[OrderOut], summary="更新订单状态（管理员）")
async def update_order_status(
    order_id: UUID,
    req: OrderStatusUpdate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    order.status = OrderStatus(req.status)
    timeline = order.timeline or []
    timeline.append({
        "status": req.status,
        "time": datetime.now(timezone.utc).isoformat(),
        "operator": str(_admin["user_id"]),
    })
    order.timeline = timeline
    flag_modified(order, "timeline")

    await db.flush()
    await db.refresh(order)
    return APIResponse.ok(data=OrderOut.model_validate(order))


@router.post("/{order_id}/pay", response_model=APIResponse[OrderOut], summary="提交支付")
async def submit_payment(
    order_id: UUID,
    req: PaymentSubmit,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(
        Order.id == order_id, Order.retailer_id == current_user["user_id"]
    ))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="订单状态不允许支付")

    order.payment_method = PaymentMethod(req.method)

    if req.method == "bank_transfer":
        if not req.bank_transfer_image:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传转账凭证")
        order.payment_evidence = req.bank_transfer_image
        # Bank transfer requires admin confirmation
        order.payment_status = PaymentStatus.PENDING
        order.status = OrderStatus.PENDING_PAYMENT
    else:
        # WeChat Pay (simulate for now — real integration in production)
        order.payment_status = PaymentStatus.PAID
        order.status = OrderStatus.PAID
        timeline = order.timeline or []
        timeline.append({"status": "paid", "time": datetime.now(timezone.utc).isoformat(), "operator": "system"})
        order.timeline = timeline
        flag_modified(order, "timeline")

    await db.flush()
    await db.refresh(order)
    return APIResponse.ok(
        data=OrderOut.model_validate(order),
        message="支付成功" if req.method == "wechat_pay" else "转账凭证已提交，等待确认"
    )


@router.post("/{order_id}/assign", response_model=APIResponse[OrderOut], summary="指派设计师（管理员）")
async def assign_designer(
    order_id: UUID,
    req: AssignDesignerRequest,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.type.value != "store_design":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅设计服务订单可指派设计师")

    # Verify designer exists
    designer_result = await db.execute(
        select(User).where(User.id == req.designer_id, User.role == UserRole.DESIGNER)
    )
    designer = designer_result.scalar_one_or_none()
    if not designer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设计师不存在")

    order.assigned_designer_id = req.designer_id
    await db.flush()
    await db.refresh(order)
    return APIResponse.ok(data=OrderOut.model_validate(order), message="设计师指派成功")
