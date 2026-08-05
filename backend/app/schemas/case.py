"""案例相关 Pydantic schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    images: list[str] = Field(..., min_length=1, description="至少一张图片")
    category_tags: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    store_area_range: str | None = None
    sort_order: int = 0
    is_featured: bool = False
    status: str = "published"


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    images: list[str] | None = None
    category_tags: list[str] | None = None
    style_tags: list[str] | None = None
    store_area_range: str | None = None
    sort_order: int | None = None
    is_featured: bool | None = None
    status: str | None = None


class CaseOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    images: list = []
    category_tags: list = []
    style_tags: list = []
    store_area_range: str | None
    sort_order: int
    is_featured: bool
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CaseListOut(BaseModel):
    """案例列表项（简化）"""
    id: UUID
    title: str
    images: list = []
    category_tags: list = []
    style_tags: list = []
    store_area_range: str | None
    is_featured: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
