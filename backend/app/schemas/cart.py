"""购物车相关 Pydantic schemas"""
from uuid import UUID
from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: UUID
    spec: str = "默认"
    quantity: int = Field(..., ge=1, description="数量 >= 1")


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="数量 >= 1")


class CartItemOut(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    image: str | None = None
    spec: str
    quantity: int
    unit_price_min: float | None = None
    unit_price_max: float | None = None
    stock: int | None = None
    min_order_qty: int

    model_config = {"from_attributes": True}
