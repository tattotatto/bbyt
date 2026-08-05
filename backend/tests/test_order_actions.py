"""订单操作测试：cancel / confirm / refund"""
import uuid
import pytest
from sqlalchemy import select
from app.models.user import User, UserRole, UserStatus
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderStatus
from app.services.auth_service import create_access_token, hash_password


async def _mk_retailer(db_session, phone: str):
    u = User(phone=phone, hashed_password=hash_password("pass1234"),
             role=UserRole.RETAILER, status=UserStatus.ACTIVE)
    db_session.add(u); await db_session.flush()
    token = create_access_token(u.id, u.role.value)
    return u, token


async def _mk_product(db_session):
    p = Product(name="泳圈", pricing_rules={"normal": [{"qty": 10, "price": 35.0}]},
                status=ProductStatus.ON_SALE, min_order_qty=10, stock=100)
    db_session.add(p); await db_session.flush()
    return p


async def _mk_order(client, token, product):
    res = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": str(product.id), "name": "泳圈", "qty": 10,
                   "unit_price": 35.0, "subtotal": 350.0}],
        "payment_method": "wechat_pay"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    return res.json()["data"]["id"]


@pytest.mark.asyncio
async def test_cancel_own_pending_order(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000011")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_other_users_order_403(client, db_session):
    u1, token1 = await _mk_retailer(db_session, "13900000012")
    u2, token2 = await _mk_retailer(db_session, "13900000013")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token1, p)
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_cancel_after_paid_is_400(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000014")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    await client.post(f"/api/v1/orders/{oid}/pay", json={"method": "wechat_pay"},
                      headers={"Authorization": f"Bearer {token}"})
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_confirm_shipped_to_completed(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000015")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    # 管理员侧置为 shipped（模拟发货）
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.SHIPPED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/confirm",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_refund_paid_to_refunding(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000016")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    await client.post(f"/api/v1/orders/{oid}/pay", json={"method": "wechat_pay"},
                      headers={"Authorization": f"Bearer {token}"})
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "refunding"
