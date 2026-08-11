"""路由尾部斜杠回归测试。

前端 API 层调用无尾部斜杠路径（/cart、/orders 等）。若后端根路由只注册
在 "/"，FastAPI 会对无斜杠路径返回 307 重定向到带斜杠路径，导致前端多一次
跳转且 POST 语义不稳定。此测试用 follow_redirects=False 断言这些路径
"直接命中路由"（未登录 → 401），而不是 307。
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_cart_root_no_trailing_slash(client, db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test",
                           follow_redirects=False) as c:
        r = await c.get("/api/v1/cart")
        assert r.status_code == 401, f"GET /api/v1/cart 应命中路由返回 401（未登录），实际 {r.status_code}"


@pytest.mark.asyncio
async def test_orders_root_no_trailing_slash(client, db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test",
                           follow_redirects=False) as c:
        r = await c.post("/api/v1/orders", json={})
        assert r.status_code in (401, 422), f"POST /api/v1/orders 应命中路由（401 未登录 或 422 参数校验），实际 {r.status_code}"
