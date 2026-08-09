"""微信登录测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.config import Settings


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


# ── Real WeChat jscode2session mock tests ──


class _FakeAsyncClient:
    """Mocks httpx.AsyncClient for testing the real WeChat API branch."""

    def __init__(self, response_data: dict):
        self._resp = MagicMock()
        self._resp.json.return_value = response_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url: str):
        return self._resp


@pytest.mark.asyncio
async def test_wx_login_real_wechat_success(client, db_session, monkeypatch):
    """真实微信 jscode2session 成功返回 openid"""
    monkeypatch.setattr(
        "app.api.auth.get_settings",
        lambda: Settings(WECHAT_APPID="wx_test_appid", WECHAT_SECRET="wx_test_secret"),
    )
    monkeypatch.setattr(
        "app.api.auth.httpx",
        type("_PatchedHttpx", (), {
            "AsyncClient": lambda: _FakeAsyncClient(
                {"openid": "wx_real_openid_123", "session_key": "sk_xxx"}
            )
        }),
    )

    res = await client.post("/api/v1/auth/wx-login",
        json={"code": "061abc123", "user_info": {"nickName": "真实用户"}})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["access_token"]
    assert data["user_info"]["nickname"] == "真实用户"


@pytest.mark.asyncio
async def test_wx_login_real_wechat_errcode(client, db_session, monkeypatch):
    """真实微信 jscode2session 返回 errcode != 0 → 401"""
    monkeypatch.setattr(
        "app.api.auth.get_settings",
        lambda: Settings(WECHAT_APPID="wx_test_appid", WECHAT_SECRET="wx_test_secret"),
    )
    monkeypatch.setattr(
        "app.api.auth.httpx",
        type("_PatchedHttpx", (), {
            "AsyncClient": lambda: _FakeAsyncClient(
                {"errcode": 40029, "errmsg": "invalid code"}
            )
        }),
    )

    res = await client.post("/api/v1/auth/wx-login",
        json={"code": "bad_code"})
    assert res.status_code == 401
    assert "invalid code" in res.json()["detail"]


@pytest.mark.asyncio
async def test_wx_login_real_wechat_network_error(client, db_session, monkeypatch):
    """真实微信 jscode2session 网络异常 → 502"""
    monkeypatch.setattr(
        "app.api.auth.get_settings",
        lambda: Settings(WECHAT_APPID="wx_test_appid", WECHAT_SECRET="wx_test_secret"),
    )

    class _FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str):
            raise ConnectionError("DNS lookup failed")

    monkeypatch.setattr(
        "app.api.auth.httpx",
        type("_PatchedHttpx", (), {"AsyncClient": lambda: _FailingClient()}),
    )

    res = await client.post("/api/v1/auth/wx-login",
        json={"code": "any_code"})
    assert res.status_code == 502
    assert "DNS lookup failed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_wx_login_real_wechat_same_openid_same_user(client, db_session, monkeypatch):
    """真实微信模式：同一 openid 返回同一用户"""
    monkeypatch.setattr(
        "app.api.auth.get_settings",
        lambda: Settings(WECHAT_APPID="wx_test_appid", WECHAT_SECRET="wx_test_secret"),
    )
    monkeypatch.setattr(
        "app.api.auth.httpx",
        type("_PatchedHttpx", (), {
            "AsyncClient": lambda: _FakeAsyncClient(
                {"openid": "wx_same_user_test", "session_key": "sk"}
            )
        }),
    )

    r1 = await client.post("/api/v1/auth/wx-login", json={"code": "c1"})
    r2 = await client.post("/api/v1/auth/wx-login", json={"code": "c2"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["data"]["user_info"]["id"] == r2.json()["data"]["user_info"]["id"]


@pytest.mark.asyncio
async def test_pending_review_user_can_refresh(client, db_session):
    """PENDING_REVIEW 用户应能正常刷新 token（不被强制 401）"""
    # dev 登录建 pending_review 用户拿 refresh_token
    login = await client.post("/api/v1/auth/wx-login", json={"code": "dev_refresh"})
    rt = login.json()["data"]["refresh_token"]
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert res.status_code == 200
    assert res.json()["data"]["access_token"]
