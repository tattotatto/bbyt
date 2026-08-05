"""认证相关 API 端点"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
import httpx
from app.database import get_db
from app.models.user import User, UserRole, UserStatus, RetailerProfile, RetailerLevel
from app.schemas.user import (
    RetailerRegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserOut,
    WxLoginRequest, WxLoginResult,
)
from app.schemas.common import APIResponse
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_refresh_token,
)
from app.api.deps import get_current_user
from app.config import get_settings

router = APIRouter()


@router.post("/register", response_model=APIResponse[UserOut], summary="零售商注册")
async def register(req: RetailerRegisterRequest, db: AsyncSession = Depends(get_db)):
    # 1. Check phone uniqueness
    existing = await db.execute(select(User).where(User.phone == req.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该手机号已注册")

    # 2. Create user
    user = User(
        phone=req.phone,
        hashed_password=hash_password(req.password),
        role=UserRole.RETAILER,
        level=RetailerLevel.NORMAL,
        status=UserStatus.PENDING_REVIEW,  # 需要管理员审核
    )
    db.add(user)
    await db.flush()  # 获取 user.id

    # 3. Create retailer profile
    profile = RetailerProfile(
        user_id=user.id,
        user=user,  # explicitly link for back_populates, avoids lazy load
        company_name=req.company_name,
        business_license=req.business_license,
        contact_person=req.contact_person,
    )
    db.add(profile)
    await db.flush()

    return APIResponse.ok(data=UserOut.model_validate(user), message="注册成功，请等待管理员审核")


@router.post("/login", response_model=APIResponse[TokenResponse], summary="手机号+密码登录")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Find user
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误")

    # 2. Check status
    if user.status == UserStatus.FROZEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被冻结，请联系管理员")
    if user.status == UserStatus.PENDING_REVIEW:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号正在审核中，请耐心等待")

    # 3. Generate tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    return APIResponse.ok(data=TokenResponse(access_token=access_token, refresh_token=refresh_token))


@router.post("/refresh", response_model=APIResponse[TokenResponse], summary="刷新Token")
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_refresh_token(req.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token无效或已过期")

    user_id = uuid.UUID(payload.get("sub"))
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已被禁用")

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    return APIResponse.ok(data=TokenResponse(access_token=access_token, refresh_token=refresh_token))


@router.post("/wx-login", response_model=APIResponse[WxLoginResult], summary="微信小程序登录")
async def wx_login(req: WxLoginRequest, db: AsyncSession = Depends(get_db)):
    """微信 code 换 openid，创建或返回用户，签发 JWT"""
    settings = get_settings()

    # 1. Determine openid: dev mode or real WeChat API
    if not settings.WECHAT_APPID or req.code.startswith("dev_"):
        openid = settings.WX_DEV_CODE_PREFIX + req.code
    else:
        url = (
            f"https://api.weixin.qq.com/sns/jscode2session"
            f"?appid={settings.WECHAT_APPID}"
            f"&secret={settings.WECHAT_SECRET}"
            f"&js_code={req.code}"
            f"&grant_type=authorization_code"
        )
        async with httpx.AsyncClient() as http:
            resp = await http.get(url)
            wx_data = resp.json()
        if wx_data.get("errcode", 0) != 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"微信登录失败: {wx_data.get('errmsg', '未知错误')}",
            )
        openid = wx_data["openid"]

    # 2. Find or create user by wx_openid
    result = await db.execute(
        select(User)
        .options(selectinload(User.retailer_profile))
        .where(User.wx_openid == openid)
    )
    user = result.scalar_one_or_none()

    if not user:
        nickname = None
        avatar = None
        if req.user_info:
            nickname = req.user_info.get("nickName")
            avatar = req.user_info.get("avatarUrl")
        user = User(
            phone=f"wx_{openid}"[:20],
            wx_openid=openid,
            nickname=nickname,
            avatar=avatar,
            hashed_password=hash_password(uuid.uuid4().hex),
            role=UserRole.RETAILER,
            level=RetailerLevel.NORMAL,
            status=UserStatus.PENDING_REVIEW,
        )
        db.add(user)
        await db.flush()
        # Re-query with eager loading so model_validate works without greenlet
        result = await db.execute(
            select(User)
            .options(selectinload(User.retailer_profile))
            .where(User.id == user.id)
        )
        user = result.scalar_one()

    # 3. Generate tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    return APIResponse.ok(data=WxLoginResult(
        access_token=access_token,
        refresh_token=refresh_token,
        user_info=UserOut.model_validate(user),
    ))
