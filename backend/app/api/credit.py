"""账期管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.bill import CreditBill, BillStatus
from app.schemas.credit import CreditBalanceOut, BillOut, RepayRequest
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.credit import get_balance, freeze_credit
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.get("/balance", response_model=APIResponse[CreditBalanceOut], summary="当前账期额度")
async def credit_balance(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    balance = await get_balance(current_user["user_id"], db)
    return APIResponse.ok(data=balance)


@router.get("/bills", response_model=APIResponse[PaginatedResponse[BillOut]], summary="账单列表")
async def list_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CreditBill).where(CreditBill.retailer_id == current_user["user_id"])
    count_query = select(func.count()).select_from(CreditBill).where(CreditBill.retailer_id == current_user["user_id"])

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(CreditBill.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    bills = result.scalars().all()

    items = [
        BillOut(
            id=b.id,
            bill_month=b.bill_month,
            total_credit_used=b.total_credit_used,
            total_repaid=b.total_repaid,
            status=b.status.value if hasattr(b.status, 'value') else b.status,
            due_date=b.due_date,
        )
        for b in bills
    ]
    return APIResponse.ok(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("/repay", response_model=APIResponse[dict], summary="还款")
async def repay(
    req: RepayRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditBill).where(
            CreditBill.id == req.bill_id, CreditBill.retailer_id == current_user["user_id"]
        )
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该账单已还清")

    bill.total_repaid += req.amount
    if bill.total_repaid >= bill.total_credit_used:
        bill.status = BillStatus.PAID
        # 恢复额度
        from app.models.user import User
        user_result = await db.execute(select(User).where(User.id == current_user["user_id"]))
        user = user_result.scalar_one_or_none()
        if user:
            user.credit_balance = max(0, user.credit_balance - req.amount)

    await db.flush()
    return APIResponse.ok(message="还款成功")
