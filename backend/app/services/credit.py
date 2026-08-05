"""账期服务"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.bill import CreditBill, BillStatus


async def check_credit(user_id: uuid.UUID, amount: int, db: AsyncSession) -> bool:
    """检查是否可以使用账期支付"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    available = user.credit_limit - user.credit_balance
    return available >= amount


async def freeze_credit(user_id: uuid.UUID, amount: int, db: AsyncSession):
    """下单时冻结账期额度"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.credit_balance += amount
        await db.flush()


async def get_balance(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """获取当前额度信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"credit_limit": 0, "credit_balance": 0, "available": 0}
    return {
        "credit_limit": user.credit_limit,
        "credit_balance": user.credit_balance,
        "available": max(0, user.credit_limit - user.credit_balance),
    }
