"""用户画像测试"""
import pytest
import uuid as uuid_mod


def test_default_profile_structure():
    from app.services.profile import DEFAULT_PROFILE
    assert "category_preference" in DEFAULT_PROFILE
    assert "age_range_preference" in DEFAULT_PROFILE
    assert "price_band" in DEFAULT_PROFILE
    assert "purchase_cycle_days" in DEFAULT_PROFILE
    assert "seasonal_preference" in DEFAULT_PROFILE
    assert "last_updated" in DEFAULT_PROFILE


def test_get_profile_for_ai_empty():
    from app.services.profile import get_profile_for_ai
    assert get_profile_for_ai(None) == ""
    assert get_profile_for_ai({}) == ""


def test_get_profile_for_ai_with_data():
    from app.services.profile import get_profile_for_ai
    profile = {
        "category_preference": {"cat1": 0.7},
        "age_range_preference": {"3-6岁": 5},
        "purchase_cycle_days": 14,
        "quantity_preference": 50,
    }
    result = get_profile_for_ai(profile)
    assert "偏好品类" in result
    assert "3-6岁" in result
    assert "14天" in result
    assert "50件" in result


@pytest.mark.asyncio
async def test_compute_empty_profile(client):
    """无订单历史的用户 → 返回默认画像"""
    from app.services.profile import compute_user_profile
    from app.database import async_session_factory

    async with async_session_factory() as session:
        profile = await compute_user_profile(uuid_mod.uuid4(), session)
        assert profile["category_preference"] == {}
        assert profile["purchase_cycle_days"] == 30
        assert profile["last_updated"] is not None


@pytest.mark.asyncio
async def test_compute_profile_with_orders(client):
    """有订单历史的用户 → 画像包含品类偏好"""
    from app.models.user import User, UserRole, UserStatus, RetailerProfile
    from app.models.product import Category, Product, ProductStatus
    from app.models.order import Order, OrderType, OrderStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from app.services.profile import compute_user_profile

    async with async_session_factory() as session:
        # 创建用户
        user_id = uuid_mod.uuid4()
        user = User(
            phone="13900139010",
            hashed_password=hash_password("test"),
            role=UserRole.RETAILER,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        rp = RetailerProfile(
            user_id=user_id,
            company_name="测试公司",
            business_license="123",
            contact_person="测试",
        )
        session.add(rp)

        # 创建品类+商品
        cat = Category(id=uuid_mod.uuid4(), name="游泳设备")
        session.add(cat)
        product = Product(
            id=uuid_mod.uuid4(),
            category_id=cat.id,
            name="儿童游泳圈",
            pricing_rules={"normal": [{"qty": 10, "price": 30}]},
            stock=1000,
            min_order_qty=10,
            status=ProductStatus.ON_SALE,
            age_range="3-6岁",
        )
        session.add(product)
        await session.flush()

        # 创建已完成订单
        order = Order(
            order_no="HX_TEST_001",
            type=OrderType.PHYSICAL_GOODS,
            retailer_id=user_id,
            items=[{
                "product_id": str(product.id),
                "name": "儿童游泳圈",
                "qty": 50,
                "unit_price": 25,
                "subtotal": 1250,
            }],
            total_amount=125000,
            pricing_snapshot={},
            status=OrderStatus.COMPLETED,
            payment_method="wechat_pay",
            payment_status="paid",
        )
        session.add(order)
        await session.flush()

        # 计算画像
        profile = await compute_user_profile(user_id, session)
        assert profile["category_preference"] != {}
        assert profile["quantity_preference"] == 50
