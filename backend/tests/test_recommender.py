"""推荐引擎测试"""
import pytest


def test_recommender_import():
    from app.services.recommender import get_homepage_recommendations, get_restock_suggestions
    assert callable(get_homepage_recommendations)
    assert callable(get_restock_suggestions)


@pytest.mark.asyncio
async def test_recommendations_for_new_user(client, db_session):
    """新用户首页推荐+补货建议"""
    from app.models.user import User, UserStatus
    from sqlalchemy import select

    phone = "13900139030"
    # 注册
    resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "password": "test123456",
        "company_name": "test", "business_license": "123", "contact_person": "test",
    })
    assert resp.status_code == 200

    # 审核通过（使用 db_session fixture）
    result = await db_session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one()
    user.status = UserStatus.ACTIVE
    await db_session.commit()

    # 登录
    resp = await client.post("/api/v1/auth/login", json={"phone": phone, "password": "test123456"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 首页推荐
    resp = await client.get("/api/v1/recommendations/homepage", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)

    # 补货建议
    resp = await client.get("/api/v1/recommendations/restock", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)
