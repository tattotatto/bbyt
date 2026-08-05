"""购物车 API 测试"""
import uuid, pytest
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
async def test_cart_add_and_accumulate(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000021")
    p = await _mk_product(db_session)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/api/v1/cart", json={"product_id": str(p.id), "quantity": 5}, headers=h)
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/cart", json={"product_id": str(p.id), "quantity": 3}, headers=h)
    assert r2.status_code == 200
    res = await client.get("/api/v1/cart", headers=h)
    items = res.json()["data"]
    assert len(items) == 1 and items[0]["quantity"] == 8
    assert items[0]["name"] == "泳圈"
    assert items[0]["unit_price_min"] == 35.0


@pytest.mark.asyncio
async def test_cart_update_quantity(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000022")
    p = await _mk_product(db_session)
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/cart", json={"product_id": str(p.id), "quantity": 5}, headers=h)
    items = (await client.get("/api/v1/cart", headers=h)).json()["data"]
    cid = items[0]["id"]
    res = await client.put(f"/api/v1/cart/{cid}", json={"quantity": 20}, headers=h)
    assert res.status_code == 200
    assert res.json()["data"]["quantity"] == 20


@pytest.mark.asyncio
async def test_cart_delete_and_clear(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000023")
    p1 = await _mk_product(db_session, "泳圈A")
    p2 = await _mk_product(db_session, "泳圈B")
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/cart", json={"product_id": str(p1.id), "quantity": 1}, headers=h)
    await client.post("/api/v1/cart", json={"product_id": str(p2.id), "quantity": 1}, headers=h)
    items = (await client.get("/api/v1/cart", headers=h)).json()["data"]
    await client.delete(f"/api/v1/cart/{items[0]['id']}", headers=h)
    after = (await client.get("/api/v1/cart", headers=h)).json()["data"]
    assert len(after) == 1
    await client.delete("/api/v1/cart", headers=h)
    assert (await client.get("/api/v1/cart", headers=h)).json()["data"] == []


@pytest.mark.asyncio
async def test_cart_cannot_touch_others(client, db_session):
    u1, token1 = await _mk_retailer(db_session, "13900000024")
    u2, token2 = await _mk_retailer(db_session, "13900000025")
    p = await _mk_product(db_session)
    await client.post("/api/v1/cart", json={"product_id": str(p.id), "quantity": 2},
                      headers={"Authorization": f"Bearer {token1}"})
    items = (await client.get("/api/v1/cart",
                              headers={"Authorization": f"Bearer {token1}"})).json()["data"]
    cid = items[0]["id"]
    res = await client.put(f"/api/v1/cart/{cid}", json={"quantity": 9},
                           headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403
    res = await client.delete(f"/api/v1/cart/{cid}",
                              headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_cart_requires_auth(client, db_session):
    res = await client.get("/api/v1/cart")
    assert res.status_code == 401
