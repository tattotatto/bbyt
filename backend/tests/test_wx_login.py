"""微信登录测试"""
import pytest


@pytest.mark.asyncio
async def test_wx_login_dev_mode_creates_pending_review_user(client, db_session):
    """dev 模式微信登录：创建 pending_review 用户并返回 tokens"""
    res = await client.post("/api/v1/auth/wx-login",
        json={"code": "dev_abc123", "user_info": {"nickName": "测试"}})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["access_token"] and data["refresh_token"]
    assert data["user_info"]["status"] == "pending_review"
    assert data["user_info"]["nickname"] == "测试"


@pytest.mark.asyncio
async def test_wx_login_same_code_same_user(client, db_session):
    """同一 code 返回同一用户"""
    r1 = await client.post("/api/v1/auth/wx-login", json={"code": "dev_dup"})
    r2 = await client.post("/api/v1/auth/wx-login", json={"code": "dev_dup"})
    assert r1.json()["data"]["user_info"]["id"] == r2.json()["data"]["user_info"]["id"]
