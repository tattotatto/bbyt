"""购物车模型"""
import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, comment="商品ID"
    )
    spec: Mapped[str] = mapped_column(
        String(100), default="默认", nullable=False, comment="规格"
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="数量"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "spec", name="uq_cart_user_product_spec"),
    )

    product: Mapped["Product"] = relationship("Product", lazy="selectin")
