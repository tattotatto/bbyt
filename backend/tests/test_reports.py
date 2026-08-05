import pytest


@pytest.mark.asyncio
async def test_purchase_report_empty(client):
    """无订单用户 → 返回默认报告"""
    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from sqlalchemy import select

    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13900139050", "password": "test123456",
        "company_name": "test", "business_license": "123", "contact_person": "test",
    })
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13900139050"))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()
    resp = await client.post("/api/v1/auth/login", json={"phone": "13900139050", "password": "test123456"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/reports/purchase", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["order_count"] == 0
