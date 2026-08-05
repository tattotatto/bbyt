"""用户模型：平台所有角色统一在 users 表，通过 role 字段区分"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, ForeignKey, Uuid, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RETAILER = "retailer"
    OPERATOR = "operator"
    DESIGNER = "designer"


class RetailerLevel(str, enum.Enum):
    NORMAL = "normal"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class UserStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    FROZEN = "frozen"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    wx_openid: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, comment="微信OpenID")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="用户昵称")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="头像URL")
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.RETAILER, nullable=False)
    level: Mapped[RetailerLevel] = mapped_column(SAEnum(RetailerLevel), default=RetailerLevel.NORMAL, nullable=False, comment="零售商等级")
    credit_limit: Mapped[int] = mapped_column(Integer, default=0, comment="账期总额度(分)")
    credit_balance: Mapped[int] = mapped_column(Integer, default=0, comment="已用额度(分)")
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.PENDING_REVIEW, nullable=False)

    # Relations
    retailer_profile: Mapped["RetailerProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    designer_profile: Mapped["DesignerProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class RetailerProfile(Base, TimestampMixin):
    __tablename__ = "retailer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="公司名称")
    business_license: Mapped[str] = mapped_column(String(100), nullable=False, comment="营业执照号")
    contact_person: Mapped[str] = mapped_column(String(50), nullable=False, comment="联系人")
    purchase_history_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="AI生成的购买画像摘要")
    preferred_categories: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="偏好品类ID列表")

    user: Mapped["User"] = relationship(back_populates="retailer_profile")


class DesignerProfile(Base, TimestampMixin):
    __tablename__ = "designer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), unique=True, nullable=False)
    portfolio: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="作品集")
    specializations: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="擅长领域")
    active_orders_count: Mapped[int] = mapped_column(Integer, default=0, comment="进行中的订单数")

    user: Mapped["User"] = relationship(back_populates="designer_profile")
