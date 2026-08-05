"""模型测试：验证新增模型(CartItem, Address, BrowseHistory, Favorite)及扩展字段"""
import pytest
import uuid
from app.models.cart import CartItem
from app.models.address import Address
from app.models.history import BrowseHistory
from app.models.favorite import Favorite
from app.models.user import User
from app.models.product import Product, ProductStatus
from app.models.order import OrderStatus


@pytest.mark.asyncio
async def test_new_models_insert_and_enum_value(client, db_session):
    u = User(phone="13900000001", hashed_password="x")
    db_session.add(u)
    await db_session.flush()

    db_session.add(CartItem(user_id=u.id, product_id=uuid.uuid4(), quantity=5))
    db_session.add(Address(user_id=u.id, name="张三", phone="13900000001",
                           province="省", city="市", district="区", detail="路1号"))
    db_session.add(BrowseHistory(user_id=u.id, product_id=uuid.uuid4()))
    db_session.add(Favorite(user_id=u.id, product_id=uuid.uuid4()))
    p = Product(name="测试商品", pricing_rules={"normal": [{"qty": 10, "price": 1.0}]},
                status=ProductStatus.ON_SALE)
    db_session.add(p)
    await db_session.flush()

    assert OrderStatus.REFUNDING == "refunding"
    assert p.sales_count == 0
    assert u.nickname is None
