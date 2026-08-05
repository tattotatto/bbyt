"""认证系统测试"""
import pytest
from httpx import AsyncClient

REGISTER_DATA = {
    "phone": "13800138001",
    "password": "test123456",
    "company_name": "开心母婴生活馆",
    "business_license": "91110000XXXXXXXX",
    "contact_person": "张经理",
}


@pytest.mark.asyncio
async def test_register_retailer(client: AsyncClient):
    """测试零售商注册"""
    response = await client.post("/api/v1/auth/register", json=REGISTER_DATA)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["phone"] == "13800138001"
    assert data["data"]["status"] == "pending_review"
    assert data["data"]["retailer_profile"]["company_name"] == "开心母婴生活馆"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient):
    """测试重复手机号注册"""
    # First registration
    await client.post("/api/v1/auth/register", json={**REGISTER_DATA, "phone": "13800138002"})
    # Duplicate
    response = await client.post("/api/v1/auth/register", json={**REGISTER_DATA, "phone": "13800138002"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_pending_review_rejected(client: AsyncClient):
    """测试未审核用户无法登录"""
    # Register first
    await client.post("/api/v1/auth/register", json={**REGISTER_DATA, "phone": "13800138003"})
    # Try login
    response = await client.post("/api/v1/auth/login", json={
        "phone": "13800138003", "password": "test123456"
    })
    assert response.status_code == 403
    assert "审核" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """测试未登录无法获取用户信息"""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_and_get_me(client: AsyncClient, db_session):
    """测试完整登录流程：注册→管理员审核→登录→获取个人信息"""
    from app.models.user import User, UserStatus
    from sqlalchemy import select

    # 1. Register
    resp = await client.post("/api/v1/auth/register", json={
        **REGISTER_DATA, "phone": "13800138004"
    })
    assert resp.status_code == 200

    # 2. Manually approve user (simulate admin action)
    result = await db_session.execute(select(User).where(User.phone == "13800138004"))
    user = result.scalar_one()
    user.status = UserStatus.ACTIVE
    await db_session.commit()

    # 3. Login
    resp = await client.post("/api/v1/auth/login", json={
        "phone": "13800138004", "password": "test123456"
    })
    assert resp.status_code == 200
    token_data = resp.json()["data"]
    assert token_data["access_token"]
    assert token_data["token_type"] == "bearer"

    # 4. Get /me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    me = resp.json()["data"]
    assert me["phone"] == "13800138004"
    assert me["status"] == "active"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db_session):
    """测试Token刷新"""
    from app.models.user import User, UserStatus
    from sqlalchemy import select

    # Register + approve + login
    resp = await client.post("/api/v1/auth/register", json={
        **REGISTER_DATA, "phone": "13800138005"
    })
    result = await db_session.execute(select(User).where(User.phone == "13800138005"))
    user = result.scalar_one()
    user.status = UserStatus.ACTIVE
    await db_session.commit()

    resp = await client.post("/api/v1/auth/login", json={
        "phone": "13800138005", "password": "test123456"
    })
    refresh_token = resp.json()["data"]["refresh_token"]

    # Refresh
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_data = resp.json()["data"]
    assert new_data["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """测试错误密码"""
    await client.post("/api/v1/auth/register", json={
        **REGISTER_DATA, "phone": "13800138006"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "phone": "13800138006", "password": "wrong_password"
    })
    assert resp.status_code == 401
