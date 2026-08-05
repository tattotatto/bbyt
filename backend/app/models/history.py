"""浏览记录模型"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class BrowseHistory(Base, TimestampMixin):
    __tablename__ = "browse_histories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, comment="商品ID"
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="最近浏览时间"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_history_user_product"),
    )

    product: Mapped["Product"] = relationship("Product", lazy="selectin")
