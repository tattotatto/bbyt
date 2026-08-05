"""订单系统测试"""
import pytest
from httpx import AsyncClient


async def setup_order_test(client: AsyncClient) -> tuple[str, str, str]:
    """
    Helper: create admin, category, and an on-sale product.
    Returns (admin_token, retailer_token, product_id)
    """
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138020"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                phone="13800138020", hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN, status=UserStatus.ACTIVE,
            )
            session.add(admin)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138020", "password": "admin123"})
    admin_token = resp.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create category
    resp = await client.post("/api/v1/products/categories", json={"name": "测试品类"}, headers=admin_headers)
    cat_id = resp.json()["data"]["id"]

    # Create product
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "测试儿童游泳圈",
        "stock": 500,
        "min_order_qty": 10,
        "pricing_rules": {
            "gold": [{"qty": 10, "price": 25.0}, {"qty": 50, "price": 20.0}],
            "normal": [{"qty": 10, "price": 32.0}, {"qty": 50, "price": 27.0}],
        }
    }, headers=admin_headers)
    product_id = resp.json()["data"]["id"]

    # Put on sale
    await client.put(f"/api/v1/products/{product_id}/status?status_action=on_sale", headers=admin_headers)

    # Register & login retailer
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13800138021", "password": "test123456",
        "company_name": "测试公司", "business_license": "12345", "contact_person": "测试",
    })
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138021"))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138021", "password": "test123456"})
    retailer_token = resp.json()["data"]["access_token"]

    return admin_token, retailer_token, product_id


async def create_virtual_product(client: AsyncClient, admin_token: str) -> str:
    """Helper: create a virtual (store design) product and return its ID."""
    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create category
    resp = await client.post("/api/v1/products/categories", json={"name": "设计服务"}, headers=admin_headers)
    cat_id = resp.json()["data"]["id"]

    # Create virtual product
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "店面设计服务",
        "is_virtual": True,
        "min_order_qty": 1,
        "pricing_rules": {
            "normal": [{"qty": 1, "price": 5000.0}],
        }
    }, headers=admin_headers)
    product_id = resp.json()["data"]["id"]

    # Put on sale
    await client.put(f"/api/v1/products/{product_id}/status?status_action=on_sale", headers=admin_headers)

    return product_id


# ── Test 1: Create physical goods order ──
@pytest.mark.asyncio
async def test_create_physical_order(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 50, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
        "receiver_name": "张三",
        "receiver_phone": "13800000000",
        "receiver_address": "北京市朝阳区",
        "remark": "请尽快发货",
    }, headers=headers)

    assert resp.status_code == 200, f"Response: {resp.text}"
    data = resp.json()["data"]
    assert data["order_no"].startswith("HX")
    assert data["type"] == "physical_goods"
    assert data["status"] == "pending_payment"
    assert data["payment_status"] == "pending"
    assert data["total_amount"] > 0
    assert len(data["items"]) == 1
    assert data["items"][0]["qty"] == 50
    assert data["items"][0]["unit_price"] == 27.0  # normal level, 50 items → 27 yuan
    assert data["receiver_name"] == "张三"
    assert "normal" in data["pricing_snapshot"]["level"]
    assert len(data["timeline"]) == 1

    # Verify stock was deducted
    check = await client.get(f"/api/v1/products/{product_id}")
    assert check.json()["data"]["stock"] == 450  # 500 - 50


# ── Test 2: Insufficient stock → 400 ──
@pytest.mark.asyncio
async def test_create_order_insufficient_stock(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Stock is 500, try to order 1000
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 1000, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)

    assert resp.status_code == 400
    assert "库存不足" in resp.json()["detail"]


# ── Test 3: Below min order qty → 400 ──
@pytest.mark.asyncio
async def test_create_order_below_min_qty(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # min_order_qty is 10, try qty=5
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 5, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)

    assert resp.status_code == 400
    assert "低于最低起批量" in resp.json()["detail"]


# ── Test 4: Create virtual (store design) order ──
@pytest.mark.asyncio
async def test_create_store_design_order(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    virtual_id = await create_virtual_product(client, admin_token)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": virtual_id, "name": "店面设计", "qty": 1, "unit_price": 0, "subtotal": 0}],
        "payment_method": "bank_transfer",
        "store_design_detail": {"area": 200, "style": "现代简约", "budget": 500000},
    }, headers=headers)

    assert resp.status_code == 200, f"Response: {resp.text}"
    data = resp.json()["data"]
    assert data["type"] == "store_design"
    assert data["store_design_detail"] is not None

    # Virtual products should not check stock
    check = await client.get(f"/api/v1/products/{virtual_id}")
    assert check.json()["data"]["stock"] is None  # virtual product has no stock


# ── Test 5: Retailer sees only own orders ──
@pytest.mark.asyncio
async def test_list_my_orders(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create an order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 50, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # List my orders
    resp = await client.get("/api/v1/orders/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1
    order_ids = [o["id"] for o in data["items"]]
    assert order_id in order_ids


# ── Test 6: Admin can list all orders ──
@pytest.mark.asyncio
async def test_admin_list_all_orders(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {retailer_token}"}

    # Retailer creates an order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=user_headers)
    assert resp.status_code == 200

    # Admin lists all orders
    resp = await client.get("/api/v1/orders/admin", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1


# ── Test 7: Retailer cannot access admin order list ──
@pytest.mark.asyncio
async def test_retailer_cannot_access_admin_list(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    resp = await client.get("/api/v1/orders/admin", headers=headers)
    assert resp.status_code == 403


# ── Test 8: Get order detail ──
@pytest.mark.asyncio
async def test_get_order_detail(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 20, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
        "remark": "test remark",
    }, headers=headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # Get detail
    resp = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == order_id
    assert data["remark"] == "test remark"
    assert len(data["items"]) == 1


# ── Test 9: Cannot see other retailer's order ──
@pytest.mark.asyncio
async def test_cannot_see_others_order(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create order as this retailer
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    order_id = resp.json()["data"]["id"]

    # Create another retailer
    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from sqlalchemy import select

    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13800138022", "password": "test123456",
        "company_name": "另一家公司", "business_license": "67890", "contact_person": "李四",
    })
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == "13800138022"))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": "13800138022", "password": "test123456"})
    other_token = resp.json()["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Try to access the first retailer's order
    resp = await client.get(f"/api/v1/orders/{order_id}", headers=other_headers)
    assert resp.status_code == 403


# ── Test 10: Submit WeChat payment ──
@pytest.mark.asyncio
async def test_submit_payment_wechat(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # Pay
    resp = await client.post(f"/api/v1/orders/{order_id}/pay", json={
        "method": "wechat_pay",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "paid"
    assert data["payment_status"] == "paid"
    assert "支付成功" in resp.json()["message"]


# ── Test 11: Submit bank transfer payment ──
@pytest.mark.asyncio
async def test_submit_payment_bank_transfer(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "bank_transfer",
    }, headers=headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # Submit bank transfer without image → should fail
    resp = await client.post(f"/api/v1/orders/{order_id}/pay", json={
        "method": "bank_transfer",
    }, headers=headers)
    assert resp.status_code == 400
    assert "转账凭证" in resp.json()["detail"]

    # Submit with image
    resp = await client.post(f"/api/v1/orders/{order_id}/pay", json={
        "method": "bank_transfer",
        "bank_transfer_image": "https://example.com/receipt.jpg",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Status stays pending_payment until admin confirms
    assert data["status"] == "pending_payment"
    assert data["payment_evidence"] == "https://example.com/receipt.jpg"
    assert "等待确认" in resp.json()["message"]


# ── Test 12: Admin update order status ──
@pytest.mark.asyncio
async def test_admin_update_status(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create and pay order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=user_headers)
    order_id = resp.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/pay", json={"method": "wechat_pay"}, headers=user_headers)

    # Admin updates to shipped
    resp = await client.put(f"/api/v1/orders/{order_id}/status", json={
        "status": "shipped",
    }, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "shipped"

    # Admin updates to confirmed
    resp = await client.put(f"/api/v1/orders/{order_id}/status", json={
        "status": "confirmed",
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "confirmed"

    # Admin updates to completed
    resp = await client.put(f"/api/v1/orders/{order_id}/status", json={
        "status": "completed",
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"

    # Verify timeline has all status changes
    data = resp.json()["data"]
    assert len(data["timeline"]) >= 4  # pending_payment + paid + shipped + confirmed + completed


# ── Test 13: Admin cancel order ──
@pytest.mark.asyncio
async def test_admin_cancel_order(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=user_headers)
    order_id = resp.json()["data"]["id"]

    # Admin cancels
    resp = await client.put(f"/api/v1/orders/{order_id}/status", json={
        "status": "cancelled",
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "cancelled"


# ── Test 14: Assign designer ──
@pytest.mark.asyncio
async def test_assign_designer(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    virtual_id = await create_virtual_product(client, admin_token)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create a designer
    from app.models.user import User, UserRole, UserStatus, DesignerProfile
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        designer = User(
            phone="13800138030", hashed_password=hash_password("design123"),
            role=UserRole.DESIGNER, status=UserStatus.ACTIVE,
        )
        session.add(designer)
        await session.flush()
        designer_id = str(designer.id)
        profile = DesignerProfile(user_id=designer.id, portfolio={}, specializations=["店面设计"], active_orders_count=0)
        session.add(profile)
        await session.commit()

    # Create a store design order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": virtual_id, "name": "店面设计", "qty": 1, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
        "store_design_detail": {"area": 150},
    }, headers=user_headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # Assign designer
    resp = await client.post(f"/api/v1/orders/{order_id}/assign", json={
        "designer_id": designer_id,
    }, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["assigned_designer_id"] == designer_id
    assert "指派成功" in resp.json()["message"]


# ── Test 15: Assign designer to non-design order → 400 ──
@pytest.mark.asyncio
async def test_assign_designer_to_non_design_order(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create a physical goods order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=user_headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["id"]

    # Try to assign designer → should fail
    resp = await client.post(f"/api/v1/orders/{order_id}/assign", json={
        "designer_id": "00000000-0000-0000-0000-000000000001",
    }, headers=admin_headers)
    assert resp.status_code == 400
    assert "仅设计服务订单" in resp.json()["detail"]


# ── Test 16: Filter orders by status ──
@pytest.mark.asyncio
async def test_filter_orders_by_status(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create an order
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    assert resp.status_code == 200

    # Filter by pending_payment
    resp = await client.get("/api/v1/orders/?status=pending_payment", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data["items"]:
        assert item["status"] == "pending_payment"

    # Filter by non-existent status
    resp = await client.get("/api/v1/orders/?status=completed", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 0


# ── Test 17: Price snapshot is captured correctly ──
@pytest.mark.asyncio
async def test_price_snapshot_correct(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 50, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    snapshot = data["pricing_snapshot"]
    assert snapshot["level"] == "normal"
    assert product_id in snapshot["items"]
    assert snapshot["items"][product_id]["qty"] == 50
    assert snapshot["items"][product_id]["unit_price"] == 27.0
    assert "pricing_rules" in snapshot["items"][product_id]


# ── Test 18: Order requires authentication ──
@pytest.mark.asyncio
async def test_order_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": "fake-id", "name": "test", "qty": 1, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    })
    assert resp.status_code == 401


# ── Test 19: Payment on non-pending order fails ──
@pytest.mark.asyncio
async def test_payment_on_wrong_status(client: AsyncClient):
    admin_token, retailer_token, product_id = await setup_order_test(client)
    headers = {"Authorization": f"Bearer {retailer_token}"}

    # Create and pay order (becomes "paid")
    resp = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": product_id, "name": "儿童游泳圈", "qty": 10, "unit_price": 0, "subtotal": 0}],
        "payment_method": "wechat_pay",
    }, headers=headers)
    order_id = resp.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/pay", json={"method": "wechat_pay"}, headers=headers)

    # Try to pay again
    resp = await client.post(f"/api/v1/orders/{order_id}/pay", json={"method": "wechat_pay"}, headers=headers)
    assert resp.status_code == 400
    assert "状态不允许" in resp.json()["detail"]
