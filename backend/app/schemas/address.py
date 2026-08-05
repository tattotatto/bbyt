"""收货地址相关 Pydantic schemas"""
from uuid import UUID
from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    name: str = Field(..., max_length=50, description="收货人姓名")
    phone: str = Field(..., max_length=20, description="收货人电话")
    province: str = Field(..., max_length=20, description="省")
    city: str = Field(..., max_length=20, description="市")
    district: str = Field(..., max_length=20, description="区")
    detail: str = Field(..., max_length=200, description="详细地址")
    is_default: bool = Field(False, description="是否默认地址")


class AddressUpdate(BaseModel):
    name: str | None = Field(None, max_length=50, description="收货人姓名")
    phone: str | None = Field(None, max_length=20, description="收货人电话")
    province: str | None = Field(None, max_length=20, description="省")
    city: str | None = Field(None, max_length=20, description="市")
    district: str | None = Field(None, max_length=20, description="区")
    detail: str | None = Field(None, max_length=200, description="详细地址")
    is_default: bool | None = Field(None, description="是否默认地址")


class AddressOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool

    model_config = {"from_attributes": True}
