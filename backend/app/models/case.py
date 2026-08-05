"""设计案例图库模型"""
from sqlalchemy import String, Integer, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class DesignCase(Base, TimestampMixin):
    __tablename__ = "design_cases"

    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="案例标题")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="案例描述")
    images: Mapped[list] = mapped_column(JSON, nullable=False, comment="案例图片URL列表(支持多张)")
    category_tags: Mapped[list] = mapped_column(JSON, nullable=False, comment='分类标签: ["婴童游泳馆","母婴生活馆","儿童乐园"]')
    style_tags: Mapped[list] = mapped_column(JSON, nullable=False, comment='风格标签: ["ins风","自然原木","卡通童趣"]')
    store_area_range: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="面积范围: 50-100㎡/100-200㎡/200㎡+")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序权重(越大越靠前)")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否精选(决定首页展示)")
    status: Mapped[str] = mapped_column(String(20), default="published", comment="published|draft")
