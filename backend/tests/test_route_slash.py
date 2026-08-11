"""路由尾部斜杠回归测试。

前端（小程序/管理后台）调用 API 时不带尾部斜杠（如 /cart、/orders、/users）。
若某路由只注册在 "/"，FastAPI 会对无斜杠路径返回 307 重定向，导致前端多一次
跳转且 POST 语义不稳定。此测试遍历所有带尾斜杠的路由，断言其无斜杠形式
（follow_redirects=False）不会返回 307——即"直接命中路由"。
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
TEST_METHODS = {"GET", "POST", "PUT", "DELETE"}


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


@pytest.mark.asyncio
async def test_all_root_routes_no_307_on_no_trailing_slash(client, db_session):
    """遍历所有以 / 结尾的路由，断言其无斜杠形式不返回 307（系统性防回归）。"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test",
                           follow_redirects=False) as c:
        offenders = []
        for route in app.routes:
            path = getattr(route, "path", None)
            if not isinstance(path, str) or not path.endswith("/") or path == "/":
                continue
            no_slash = path[:-1]
            methods = getattr(route, "methods", None) or {"GET"}
            for m in sorted(methods & TEST_METHODS):
                r = await c.request(m, no_slash, json={} if m in BODY_METHODS else None)
                if r.status_code == 307:
                    offenders.append(f"{m} {no_slash}")
        assert not offenders, f"以下无斜杠路径返回 307（需补 '' 路由变体）：{offenders}"
