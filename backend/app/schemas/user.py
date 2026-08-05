"""用户相关 Pydantic schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ── Register ──
class RetailerRegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    company_name: str = Field(..., min_length=1, max_length=200)
    business_license: str = Field(..., min_length=1, max_length=100)
    contact_person: str = Field(..., min_length=1, max_length=50)


# ── Login ──
class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(...)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 7200


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User Output ──
class RetailerProfileOut(BaseModel):
    company_name: str
    business_license: str
    contact_person: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: UUID
    phone: str
    role: str
    level: str
    credit_limit: int
    credit_balance: int
    status: str
    nickname: str | None = None
    avatar: str | None = None
    retailer_profile: RetailerProfileOut | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    """用户列表项（管理员视角，不含敏感信息）"""
    id: UUID
    phone: str
    role: str
    level: str
    status: str
    company_name: str | None = None
    contact_person: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Admin: Review retailer ──
class ReviewRetailerRequest(BaseModel):
    user_id: UUID
    action: str = Field(..., pattern="^(approve|reject)$")
    level: str | None = Field(None, pattern="^(normal|silver|gold|platinum)$")
    credit_limit: int | None = Field(None, ge=0, description="账期额度(分)")
    reject_reason: str | None = Field(None, max_length=500)


# ── WeChat Login ──
class WxUserInfo(BaseModel):
    nickName: str | None = None
    avatarUrl: str | None = None


class WxLoginRequest(BaseModel):
    code: str
    user_info: WxUserInfo | None = None


class WxLoginResult(BaseModel):
    access_token: str
    refresh_token: str
    user_info: UserOut
