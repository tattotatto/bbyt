"""商品模型：品类（树形）、商品、定价规则（JSON）"""
import uuid
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum


class ProductStatus(str, enum.Enum):
    ON_SALE = "on_sale"
    OFF_SALE = "off_sale"
    DELETED = "deleted"


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, comment="父品类ID（树形结构）"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="品类名称")
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="图标URL")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="active|hidden")

    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", remote_side="Category.id", lazy="selectin"
    )
    parent: Mapped["Category | None"] = relationship(
        "Category", back_populates="children", remote_side=parent_id, lazy="selectin"
    )


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True, comment="所属品类"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="商品名称")
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="商品图片URL列表")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="商品描述")
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="规格参数JSON")
    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="适龄段: 0-3岁/3-6岁/6岁+")
    safety_certifications: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment='安全认证: [{"name":"3C认证","icon":"url"}]'
    )
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否虚拟商品（店面设计服务）")
    virtual_detail: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="虚拟商品详情: {area,style,budget}"
    )
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="库存（虚拟商品为null）")
    min_order_qty: Mapped[int] = mapped_column(Integer, default=10, comment="最低起批量")
    pricing_rules: Mapped[dict] = mapped_column(JSON, nullable=False, comment="阶梯定价矩阵")
    ai_knowledge_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True, comment="关联AI知识库条目(Phase 2)"
    )
    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus), default=ProductStatus.OFF_SALE, nullable=False, comment="商品状态"
    )

    category: Mapped["Category | None"] = relationship("Category", lazy="selectin")
