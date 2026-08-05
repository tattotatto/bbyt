"""商品相关 Pydantic schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ── Category ──
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: UUID | None = None
    icon: str | None = None
    sort_order: int = 0


class CategoryOut(BaseModel):
    id: UUID
    parent_id: UUID | None
    name: str
    icon: str | None
    sort_order: int
    status: str
    children: list["CategoryOut"] = []

    model_config = {"from_attributes": True}

    @field_validator("children", mode="before")
    @classmethod
    def _default_empty_list(cls, v):
        return v if v is not None else []


# ── Pricing ──
class PricingTier(BaseModel):
    """单个阶梯: {"qty": 10, "price": 80.00}"""
    qty: int = Field(..., ge=1)
    price: float = Field(..., gt=0)


class PricingRuleUpdate(BaseModel):
    """设置某个商品的价格矩阵"""
    pricing_rules: dict[str, list[PricingTier]] = Field(
        ...,
        description='{"gold": [{"qty":10,"price":80},...], "silver": [...], "normal": [...]}'
    )


class ProductPriceInfo(BaseModel):
    """根据用户等级返回的价格信息"""
    level: str
    tiers: list[PricingTier]
    matched_unit_price: float | None = Field(None, description="匹配的单价（给定数量时）")
    total_price: float | None = Field(None, description="总价（单价×数量）")


# ── Product CRUD ──
class ProductCreate(BaseModel):
    category_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    images: list[str] = []
    description: str | None = None
    specs: dict | None = None
    age_range: str | None = Field(None, description="适龄段")
    safety_certifications: list[dict] = []
    is_virtual: bool = False
    virtual_detail: dict | None = None
    stock: int | None = None
    min_order_qty: int = Field(10, ge=1)
    pricing_rules: dict[str, list[PricingTier]] = Field(
        default_factory=lambda: {"normal": [{"qty": 10, "price": 0.0}]}
    )


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = None
    images: list[str] | None = None
    description: str | None = None
    specs: dict | None = None
    age_range: str | None = None
    safety_certifications: list[dict] | None = None
    is_virtual: bool | None = None
    virtual_detail: dict | None = None
    stock: int | None = None
    min_order_qty: int | None = None
    pricing_rules: dict | None = None


class ProductOut(BaseModel):
    id: UUID
    category_id: UUID | None
    name: str
    images: list = []
    description: str | None
    specs: dict | None
    age_range: str | None
    safety_certifications: list = []
    is_virtual: bool
    virtual_detail: dict | None
    stock: int | None
    min_order_qty: int
    pricing_rules: dict
    status: str
    category: CategoryOut | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("images", "safety_certifications", mode="before")
    @classmethod
    def _default_empty_list(cls, v):
        return v if v is not None else []


class ProductListOut(BaseModel):
    """商品列表项（简化，适合Feed展示）"""
    id: UUID
    name: str
    images: list = []
    age_range: str | None
    safety_certifications: list = []
    is_virtual: bool
    stock: int | None
    min_order_qty: int
    status: str
    # 价格范围（从pricing_rules提取的最低和最高价）
    price_min: float | None = None
    price_max: float | None = None

    model_config = {"from_attributes": True}

    @field_validator("images", "safety_certifications", mode="before")
    @classmethod
    def _default_empty_list(cls, v):
        return v if v is not None else []


class ProductFilter(BaseModel):
    category_id: UUID | None = None
    age_range: str | None = None
    is_virtual: bool | None = None
    status: str | None = "on_sale"
    keyword: str | None = None
