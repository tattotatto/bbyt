"""收藏模型"""
import uuid
from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Favorite(Base, TimestampMixin):
    __tablename__ = "favorites"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, comment="商品ID"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),
    )

    product: Mapped["Product"] = relationship("Product", lazy="selectin")
