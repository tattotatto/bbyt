"""商品系统测试"""
import pytest
from httpx import AsyncClient


# ── Helpers ──
async def register_and_login(client: AsyncClient, phone: str) -> str:
    """Helper: register retailer → manually approve → login → return access_token"""
    from app.models.user import User, UserStatus
    from app.database import async_session_factory
    from sqlalchemy import select

    resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "password": "test123456",
        "company_name": "测试公司", "business_license": "123456",
        "contact_person": "测试",
    })
    assert resp.status_code == 200

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == phone))
        user = result.scalar_one()
        user.status = UserStatus.ACTIVE
        await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": phone, "password": "test123456"})
    return resp.json()["data"]["access_token"]


async def login_admin(client: AsyncClient) -> str:
    """Helper: create & login as admin"""
    from app.models.user import User, UserStatus, UserRole
    from app.database import async_session_factory
    from app.services.auth_service import hash_password

    admin_phone = "13800000001"

    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.phone == admin_phone))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                phone=admin_phone, hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN, status=UserStatus.ACTIVE,
            )
            session.add(user)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": admin_phone, "password": "admin123"})
    return resp.json()["data"]["access_token"]


# ── Category Tests ──
@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/products/categories", json={
        "name": "儿童游泳设备", "sort_order": 1
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "儿童游泳设备"


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create parent + child
    resp = await client.post("/api/v1/products/categories", json={"name": "护肤"}, headers=headers)
    parent_id = resp.json()["data"]["id"]

    await client.post("/api/v1/products/categories", json={
        "name": "防晒", "parent_id": parent_id
    }, headers=headers)

    resp = await client.get("/api/v1/products/categories")
    assert resp.status_code == 200
    categories = resp.json()["data"]
    assert len(categories) > 0


@pytest.mark.asyncio
async def test_create_category_requires_admin(client: AsyncClient):
    """非管理员不能创建品类"""
    resp = await client.post("/api/v1/products/categories", json={
        "name": "测试品类"
    })
    assert resp.status_code == 401  # No auth


# ── Product Tests ──
@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category first
    resp = await client.post("/api/v1/products/categories", json={"name": "游泳"}, headers=headers)
    cat_id = resp.json()["data"]["id"]

    # Create product
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "儿童游泳圈 小鸭子款",
        "images": ["https://example.com/img1.jpg"],
        "description": "安全环保材质，适合3-6岁宝宝",
        "age_range": "3-6岁",
        "safety_certifications": [{"name": "3C认证", "icon": "url"}],
        "stock": 500,
        "min_order_qty": 10,
        "pricing_rules": {
            "gold": [{"qty": 10, "price": 25.0}, {"qty": 50, "price": 20.0}, {"qty": 100, "price": 16.0}],
            "silver": [{"qty": 10, "price": 28.0}, {"qty": 50, "price": 23.0}, {"qty": 100, "price": 19.0}],
            "normal": [{"qty": 10, "price": 32.0}, {"qty": 50, "price": 27.0}, {"qty": 100, "price": 22.0}],
        }
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "儿童游泳圈 小鸭子款"
    assert data["age_range"] == "3-6岁"
    assert len(data["safety_certifications"]) == 1


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/products/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_product_detail(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category + product
    resp = await client.post("/api/v1/products/categories", json={"name": "健康"}, headers=headers)
    cat_id = resp.json()["data"]["id"]

    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "儿童维生素D",
        "pricing_rules": {"normal": [{"qty": 10, "price": 45.0}]},
        "min_order_qty": 10,
        "stock": 1000,
    }, headers=headers)
    product_id = resp.json()["data"]["id"]

    # Get detail (no auth needed for viewing)
    resp = await client.get(f"/api/v1/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "儿童维生素D"


@pytest.mark.asyncio
async def test_query_price(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}
    user_token = await register_and_login(client, "13900139001")

    # Create product with pricing rules
    resp = await client.post("/api/v1/products/categories", json={"name": "护肤"}, headers=headers)
    cat_id = resp.json()["data"]["id"]
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "儿童防晒霜",
        "stock": 200,
        "min_order_qty": 10,
        "pricing_rules": {
            "gold": [{"qty": 10, "price": 30.0}, {"qty": 50, "price": 24.0}],
            "normal": [{"qty": 10, "price": 38.0}, {"qty": 50, "price": 30.0}],
        }
    }, headers=headers)
    product_id = resp.json()["data"]["id"]

    # Query price as normal retailer for 50 items
    user_headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.get(f"/api/v1/products/{product_id}/price?qty=50", headers=user_headers)
    assert resp.status_code == 200
    price_info = resp.json()["data"]
    assert price_info["level"] == "normal"
    assert price_info["matched_unit_price"] == 30.0
    assert price_info["total_price"] == 1500.0


@pytest.mark.asyncio
async def test_query_price_below_min(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}
    user_token = await register_and_login(client, "13900139002")

    resp = await client.post("/api/v1/products/categories", json={"name": "玩具"}, headers=headers)
    cat_id = resp.json()["data"]["id"]
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "积木",
        "stock": 100,
        "min_order_qty": 20,
        "pricing_rules": {"normal": [{"qty": 20, "price": 15.0}]}
    }, headers=headers)
    product_id = resp.json()["data"]["id"]

    # Query with qty below minimum
    user_headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.get(f"/api/v1/products/{product_id}/price?qty=5", headers=user_headers)
    assert resp.status_code == 400  # Below minimum


@pytest.mark.asyncio
async def test_product_detail_includes_sales_count(client: AsyncClient):
    """产品详情应包含 sales_count 字段"""
    from app.models.product import Product, ProductStatus
    from app.database import async_session_factory

    async with async_session_factory() as session:
        p = Product(
            name="泳圈",
            pricing_rules={"normal": [{"qty": 10, "price": 35.0}]},
            status=ProductStatus.ON_SALE,
            min_order_qty=10,
            stock=100,
            sales_count=88,
        )
        session.add(p)
        await session.commit()
        pid = p.id

    res = await client.get(f"/api/v1/products/{pid}")
    assert res.status_code == 200
    assert res.json()["data"]["sales_count"] == 88


@pytest.mark.asyncio
async def test_update_product_status(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/products/categories", json={"name": "测试"}, headers=headers)
    cat_id = resp.json()["data"]["id"]
    resp = await client.post("/api/v1/products/", json={
        "category_id": cat_id,
        "name": "测试商品",
        "stock": 100,
        "min_order_qty": 10,
        "pricing_rules": {"normal": [{"qty": 10, "price": 10.0}]}
    }, headers=headers)
    product_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["status"] == "off_sale"  # Default off_sale

    # Put on sale
    resp = await client.put(
        f"/api/v1/products/{product_id}/status?status_action=on_sale", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "on_sale"
