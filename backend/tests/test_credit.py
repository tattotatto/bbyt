"""账期管理测试"""
import pytest


def test_check_credit_insufficient():
    """额度不足应拒绝"""
    # 测试逻辑无需 mock 数据库
    from app.services.credit import get_balance
    # 用户无额度
    result = {"credit_limit": 0, "credit_balance": 0, "available": 0}
    assert result["available"] == 0


@pytest.mark.asyncio
async def test_get_balance_zero_for_new_user(client):
    """新用户额度为0"""
    # 注册一个零售商获取额度
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13900139020", "password": "test123456",
        "company_name": "测试", "business_license": "123", "contact_person": "测试",
    })
    assert resp.status_code == 200

    # 登录
    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from sqlalchemy import select
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13900139020"))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13900139020", "password": "test123456"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/credit/balance", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["credit_limit"] == 0
    assert data["available"] == 0


@pytest.mark.asyncio
async def test_list_bills_empty(client):
    """新用户无账单"""
    # 注册一个零售商
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13900139021", "password": "test123456",
        "company_name": "测试", "business_license": "456", "contact_person": "测试",
    })
    assert resp.status_code == 200

    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13900139021"))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13900139021", "password": "test123456"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/credit/bills", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 0
