"""收藏 API 测试"""
import pytest
from app.models.user import User, UserRole, UserStatus
from app.models.product import Product, ProductStatus
from app.services.auth_service import create_access_token, hash_password


async def _mk_retailer(db_session, phone: str):
    u = User(phone=phone, hashed_password=hash_password("pass1234"),
             role=UserRole.RETAILER, status=UserStatus.ACTIVE)
    db_session.add(u); await db_session.flush()
    return u, create_access_token(u.id, u.role.value)


async def _mk_product(db_session, name="泳圈", price=35.0):
    p = Product(name=name, pricing_rules={"normal": [{"qty": 10, "price": price}]},
                status=ProductStatus.ON_SALE, min_order_qty=10, stock=100)
    db_session.add(p); await db_session.flush()
    return p


@pytest.mark.asyncio
async def test_favorite_add_idempotent_and_list(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000051")
    p = await _mk_product(db_session)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/api/v1/favorites", json={"product_id": str(p.id)}, headers=h)
    assert r1.status_code == 200
    # 重复收藏 → 幂等，不报错
    r2 = await client.post("/api/v1/favorites", json={"product_id": str(p.id)}, headers=h)
    assert r2.status_code == 200
    res = await client.get("/api/v1/favorites", headers=h)
    data = res.json()["data"]
    assert data["total"] == 1
    item = data["items"][0]
    assert item["name"] == "泳圈" and item["price_min"] == 35.0


@pytest.mark.asyncio
async def test_favorite_pagination_order(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000052")
    h = {"Authorization": f"Bearer {token}"}
    for i in range(3):
        p = await _mk_product(db_session, name=f"商品{i}")
        await client.post("/api/v1/favorites", json={"product_id": str(p.id)}, headers=h)
    res = await client.get("/api/v1/favorites?page_size=2", headers=h)
    data = res.json()["data"]
    assert data["total"] == 3 and len(data["items"]) == 2
    assert data["items"][0]["name"] == "商品2"  # created_at 倒序


@pytest.mark.asyncio
async def test_favorite_unfavorite(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000053")
    p = await _mk_product(db_session)
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/favorites", json={"product_id": str(p.id)}, headers=h)
    res = await client.delete(f"/api/v1/favorites/{p.id}", headers=h)
    assert res.status_code == 200
    assert (await client.get("/api/v1/favorites", headers=h)).json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_favorite_requires_auth(client, db_session):
    assert (await client.get("/api/v1/favorites")).status_code == 401
