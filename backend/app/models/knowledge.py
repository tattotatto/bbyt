"""知识库模型：存储商品知识条目的向量嵌入"""
import uuid
from sqlalchemy import String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge_entries"

    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="来源: product|manual|faq|conversation"
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, comment="关联商品ID"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="知识内容（原始文本，用于全文搜索）"
    )
    embedding: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="向量嵌入(1536维)，JSON存储兼容SQLite"
    )
    meta_info: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True, comment="元数据: 适龄、品类、认证等"
    )
    weight: Mapped[float] = mapped_column(
        Float, default=1.0, comment="权重（学习机制调整）"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", comment="active|deprecated"
    )
