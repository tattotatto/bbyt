"""账期相关 schemas"""
from uuid import UUID
from pydantic import BaseModel, Field


class CreditBalanceOut(BaseModel):
    credit_limit: int          # 总额度(分)
    credit_balance: int        # 已用额度(分)
    available: int             # 可用额度(分)


class BillOut(BaseModel):
    id: UUID
    bill_month: str
    total_credit_used: int
    total_repaid: int
    status: str
    due_date: str | None


class RepayRequest(BaseModel):
    bill_id: UUID
    amount: int = Field(..., gt=0, description="还款金额(分)")
