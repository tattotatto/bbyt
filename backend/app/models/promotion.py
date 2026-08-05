"""促销活动模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, JSON, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
import enum


class PromotionType(str, enum.Enum):
    FULL_REDUCTION = "full_reduction"  # 满减
    DISCOUNT = "discount"              # 折扣
    FLASH_SALE = "flash_sale"          # 限时秒杀


class Promotion(Base, TimestampMixin):
    __tablename__ = "promotions"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[PromotionType] = mapped_column(SAEnum(PromotionType), nullable=False)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False, comment="促销规则")
    # full_reduction: {"threshold": 100000, "reduce": 10000}  # 满1000减100(分)
    # discount: {"rate": 0.85}  # 85折
    # flash_sale: {"price": 5000, "limit_qty": 100}  # 秒杀价50元/限100件
    product_ids: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="适用商品ID列表(null=全场)")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
