"""账期账单模型"""
import uuid
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
import enum


class BillStatus(str, enum.Enum):
    PENDING = "pending"      # 待还款
    PAID = "paid"            # 已还款
    OVERDUE = "overdue"      # 逾期


class CreditBill(Base, TimestampMixin):
    __tablename__ = "credit_bills"

    retailer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    bill_month: Mapped[str] = mapped_column(String(7), nullable=False, comment="账单月份: 2026-07")
    total_credit_used: Mapped[int] = mapped_column(Integer, default=0, comment="本期使用额度(分)")
    total_repaid: Mapped[int] = mapped_column(Integer, default=0, comment="已还金额(分)")
    status: Mapped[BillStatus] = mapped_column(SAEnum(BillStatus), default=BillStatus.PENDING)
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="到期日")
