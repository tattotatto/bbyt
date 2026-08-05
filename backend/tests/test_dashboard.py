"""AI 看板测试"""
import pytest


@pytest.mark.asyncio
async def test_ai_overview_requires_admin(client):
    """非管理员不能访问"""
    resp = await client.get("/api/v1/dashboard/ai/overview")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ai_overview_admin(client):
    """管理员可访问 AI 概览"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    # 创建 admin
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138040"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(phone="13800138040", hashed_password=hash_password("admin123"),
                        role=UserRole.ADMIN, status=UserStatus.ACTIVE)
            session.add(admin)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138040", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/dashboard/ai/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_orders" in data
    assert "ai_orders" in data
    assert "conversion_rate" in data
    assert "kb_entries" in data
    assert "active_users" in data


@pytest.mark.asyncio
async def test_ai_trends_admin(client):
    """管理员可访问趋势数据"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138040"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(phone="13800138040", hashed_password=hash_password("admin123"),
                        role=UserRole.ADMIN, status=UserStatus.ACTIVE)
            session.add(admin)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138040", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/dashboard/ai/trends?days=7", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    # 应有 7 天的数据
    assert len(data) > 0


@pytest.mark.asyncio
async def test_model_usage_admin(client):
    """管理员可访问模型使用统计"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138040"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(phone="13800138040", hashed_password=hash_password("admin123"),
                        role=UserRole.ADMIN, status=UserStatus.ACTIVE)
            session.add(admin)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138040", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/dashboard/ai/model-usage", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "models" in data
    assert "routing" in data
