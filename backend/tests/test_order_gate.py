"""审核门禁测试"""
import pytest
from app.models.product import Product, ProductStatus


@pytest.mark.asyncio
async def test_order_gate_rejects_pending_review(client, db_session):
    """未审核用户下单应被 403 拒绝"""
    # 造一个 on_sale 商品
    p = Product(name="泳圈", pricing_rules={"normal": [{"qty": 10, "price": 35.0}]},
                status=ProductStatus.ON_SALE, min_order_qty=10, stock=100)
    db_session.add(p); await db_session.flush()

    # wx-login 建 pending_review 用户并获取 token
    wx_res = await client.post("/api/v1/auth/wx-login", json={"code": "dev_gate_test"})
    assert wx_res.status_code == 200
    token = wx_res.json()["data"]["access_token"]

    # 未审核用户下单应 403
    res = await client.post("/api/v1/orders/", json={
        "items": [{"product_id": str(p.id), "name": "泳圈", "qty": 10,
                   "unit_price": 35.0, "subtotal": 350.0}],
        "payment_method": "wechat_pay"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
