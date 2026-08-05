from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None

    @classmethod
    def ok(cls, data: T = None, message: str = "ok") -> "APIResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = -1) -> "APIResponse":
        return cls(code=code, message=message, data=None)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
