"""订单模型"""
import uuid
from sqlalchemy import String, Integer, ForeignKey, JSON, Enum as SAEnum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum


class OrderType(str, enum.Enum):
    PHYSICAL_GOODS = "physical_goods"
    STORE_DESIGN = "store_design"


class PaymentMethod(str, enum.Enum):
    WECHAT_PAY = "wechat_pay"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"  # Phase 3 full implementation


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"  # bank transfer confirmed by admin
    OVERDUE = "overdue"


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    SHIPPED = "shipped"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DesignProgress(str, enum.Enum):
    BRIEF = "brief"        # 需求对接
    DRAFT = "draft"        # 初稿
    REVISION = "revision"  # 修改中
    FINALIZED = "finalized" # 定稿


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, comment="订单号")
    type: Mapped[OrderType] = mapped_column(SAEnum(OrderType), default=OrderType.PHYSICAL_GOODS, nullable=False)
    retailer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    items: Mapped[list] = mapped_column(JSON, nullable=False, comment='订单商品列表 [{"product_id":"...","name":"...","qty":100,"unit_price":35,"subtotal":3500}]')
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="订单总额(分)")
    pricing_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, comment="下单时价格快照")
    payment_method: Mapped[PaymentMethod | None] = mapped_column(SAEnum(PaymentMethod), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_credit_used: Mapped[int] = mapped_column(Integer, default=0, comment="使用账期的金额(分)")
    payment_evidence: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="银行转账凭证URL")
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.PENDING_PAYMENT)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="买家备注")

    # 设计服务专属
    store_design_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="店面设计详情")
    assigned_designer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, comment="指派设计师")
    design_progress: Mapped[DesignProgress | None] = mapped_column(SAEnum(DesignProgress), nullable=True)

    # AI关联 (Phase 2)
    ai_conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="AI对话记录引用(Phase 2)")

    # 时间线
    timeline: Mapped[list | None] = mapped_column(JSON, nullable=True, comment='状态变更时间线 [{"status":"paid","time":"...","operator":"system"}]')

    # 收货信息
    receiver_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    receiver_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    retailer: Mapped["User"] = relationship("User", foreign_keys=[retailer_id], lazy="selectin")


from app.models.user import User
