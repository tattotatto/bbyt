"""订单相关 Pydantic schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    product_id: str
    name: str
    qty: int
    unit_price: float
    subtotal: float
    image: str | None = None


class OrderCreate(BaseModel):
    """创建订单请求"""
    items: list[OrderItem] = Field(..., min_length=1)
    payment_method: str = Field(..., pattern="^(wechat_pay|bank_transfer|credit)$")
    remark: str | None = None
    # 收货信息
    receiver_name: str | None = None
    receiver_phone: str | None = None
    receiver_address: str | None = None
    # 设计服务
    store_design_detail: dict | None = None


class OrderOut(BaseModel):
    id: UUID
    order_no: str
    type: str
    retailer_id: UUID
    items: list = []
    total_amount: int
    pricing_snapshot: dict = {}
    payment_method: str | None
    payment_status: str
    payment_credit_used: int
    payment_evidence: str | None
    status: str
    remark: str | None
    store_design_detail: dict | None
    assigned_designer_id: UUID | None
    design_progress: str | None
    receiver_name: str | None
    receiver_phone: str | None
    receiver_address: str | None
    timeline: list = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderListOut(BaseModel):
    id: UUID
    order_no: str
    type: str
    items: list = []          # 简化的商品列表
    total_amount: int
    payment_method: str | None
    payment_status: str
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(paid|shipped|confirmed|completed|cancelled)$")
    tracking_number: str | None = None


class AssignDesignerRequest(BaseModel):
    designer_id: UUID


class PaymentSubmit(BaseModel):
    method: str = Field(..., pattern="^(wechat_pay|bank_transfer)$")
    bank_transfer_image: str | None = Field(None, description="银行转账凭证URL")
