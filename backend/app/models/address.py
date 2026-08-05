"""收货地址模型"""
import uuid
from sqlalchemy import String, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="收货人姓名"
    )
    phone: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="收货人电话"
    )
    province: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="省"
    )
    city: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="市"
    )
    district: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="区"
    )
    detail: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="详细地址"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否默认地址"
    )
