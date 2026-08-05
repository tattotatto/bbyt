"""知识库 Pydantic schemas"""
from pydantic import BaseModel, Field


class KnowledgeEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    source_type: str = Field(default="manual", pattern="^(manual|faq)$")


class KnowledgeEntryOut(BaseModel):
    id: str
    title: str
    source_type: str
    weight: float
    status: str
    content: str | None = None
