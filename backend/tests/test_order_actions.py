"""订单操作测试：cancel / confirm / refund"""
import uuid
import pytest
from sqlalchemy import select
from app.models.user import User, UserRole, UserStatus
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderStatus
from app.services.auth_service import create_access_token, hash_password


async def _mk_user(db_session, phone: str, role: UserRole = UserRole.RETAILER):
    u = User(phone=phone, hashed_password=hash_password("pass1234"),
             role=role, status=UserStatus.ACTIVE)
    db_session.add(u); await db_session.flush()
    token = create_access_token(u.id, u.role.value)
    return u, token


async def _mk_retailer(db_session, phone: str):
    return await _mk_user(db_session, phone, UserRole.RETAILER)


async def _mk_admin(db_session, phone: str):
    return await _mk_user(db_session, phone, UserRole.ADMIN)


async def _mk_operator(db_session, phone: str):
    return await _mk_user(db_session, phone, UserRole.OPERATOR)


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


# ── cancel ──

@pytest.mark.asyncio
async def test_cancel_own_pending_order(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000011")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "cancelled"
    # timeline 断言
    assert data["timeline"]
    last = data["timeline"][-1]
    assert last["status"] == "cancelled"
    assert "time" in last
    assert "operator" in last


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
async def test_admin_cancel_others_order(client, db_session):
    """Important 2: admin 可取消他人订单"""
    u, token = await _mk_retailer(db_session, "13900000021")
    admin, admin_token = await _mk_admin(db_session, "13900000022")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_operator_cancel_others_order(client, db_session):
    """Important 2: operator 可取消他人订单"""
    u, token = await _mk_retailer(db_session, "13900000023")
    op, op_token = await _mk_operator(db_session, "13900000024")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/cancel",
                            headers={"Authorization": f"Bearer {op_token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "cancelled"


# ── confirm ──

@pytest.mark.asyncio
async def test_confirm_shipped_to_completed(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000015")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.SHIPPED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/confirm",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "completed"
    # timeline 断言
    last = data["timeline"][-1]
    assert last["status"] == "completed"
    assert "time" in last
    assert "operator" in last


@pytest.mark.asyncio
async def test_confirm_non_owner_403(client, db_session):
    """Important 4: confirm 越权 403"""
    u1, token1 = await _mk_retailer(db_session, "13900000031")
    u2, token2 = await _mk_retailer(db_session, "13900000032")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token1, p)
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.SHIPPED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/confirm",
                            headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_confirm_on_wrong_status_400(client, db_session):
    """Important 3: pending_payment 上 confirm 应 400"""
    u, token = await _mk_retailer(db_session, "13900000033")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/confirm",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_admin_confirm_others_order(client, db_session):
    """Important 2: admin 可确认他人订单"""
    u, token = await _mk_retailer(db_session, "13900000034")
    admin, admin_token = await _mk_admin(db_session, "13900000035")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.SHIPPED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/confirm",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "completed"


# ── refund ──

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
    data = res.json()["data"]
    assert data["status"] == "refunding"
    # timeline 断言
    last = data["timeline"][-1]
    assert last["status"] == "refunding"
    assert "time" in last
    assert "operator" in last


@pytest.mark.asyncio
async def test_refund_shipped_to_refunding(client, db_session):
    """Important 5: shipped → refunding"""
    u, token = await _mk_retailer(db_session, "13900000041")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    # 管理员侧置为 shipped
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.SHIPPED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "refunding"


@pytest.mark.asyncio
async def test_refund_non_owner_403(client, db_session):
    """Important 4: refund 越权 403"""
    u1, token1 = await _mk_retailer(db_session, "13900000042")
    u2, token2 = await _mk_retailer(db_session, "13900000043")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token1, p)
    await client.post(f"/api/v1/orders/{oid}/pay", json={"method": "wechat_pay"},
                      headers={"Authorization": f"Bearer {token1}"})
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_refund_on_pending_payment_400(client, db_session):
    """Important 3: pending_payment 上 refund 应 400"""
    u, token = await _mk_retailer(db_session, "13900000044")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_refund_on_completed_400(client, db_session):
    """Important 3: completed 上 refund 应 400"""
    u, token = await _mk_retailer(db_session, "13900000045")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    order = (await db_session.execute(
        select(Order).where(Order.id == uuid.UUID(oid)))).scalar_one()
    order.status = OrderStatus.COMPLETED
    await db_session.flush()
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_admin_refund_others_order(client, db_session):
    """Important 2: admin 可退款他人订单"""
    u, token = await _mk_retailer(db_session, "13900000046")
    admin, admin_token = await _mk_admin(db_session, "13900000047")
    p = await _mk_product(db_session)
    oid = await _mk_order(client, token, p)
    await client.post(f"/api/v1/orders/{oid}/pay", json={"method": "wechat_pay"},
                      headers={"Authorization": f"Bearer {token}"})
    res = await client.post(f"/api/v1/orders/{oid}/refund",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "refunding"
