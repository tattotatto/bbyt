"""Task A3: 商品 hot / new / sort 测试"""
import pytest
from datetime import datetime, timezone
from app.models.product import Product, ProductStatus


def make_product(name: str, price: float, sales_count: int = 0, created_at=None) -> Product:
    return Product(
        name=name,
        pricing_rules={"normal": [{"qty": 10, "price": price}]},
        status=ProductStatus.ON_SALE,
        min_order_qty=10, stock=100,
        sales_count=sales_count,
        created_at=created_at or datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_products_hot_sorted_by_sales(client, db_session):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db_session.add(make_product("低销量", 30.0, sales_count=1, created_at=base))
    db_session.add(make_product("高销量", 50.0, sales_count=999, created_at=base))
    db_session.add(make_product("中销量", 40.0, sales_count=500, created_at=base))
    await db_session.flush()
    res = await client.get("/api/v1/products/hot")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["data"]]
    assert names == ["高销量", "中销量", "低销量"]


@pytest.mark.asyncio
async def test_products_new_sorted_by_created(client, db_session):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db_session.add(make_product("旧品", 30.0, created_at=base))
    db_session.add(make_product("新品", 30.0, created_at=base.replace(month=2)))
    await db_session.flush()
    res = await client.get("/api/v1/products/new")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["data"]]
    assert names == ["新品", "旧品"]


@pytest.mark.asyncio
async def test_products_price_asc(client, db_session):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db_session.add(make_product("贵", 90.0, created_at=base))
    db_session.add(make_product("便宜", 20.0, created_at=base))
    await db_session.flush()
    res = await client.get("/api/v1/products?sort=price_asc")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["data"]["items"]]
    assert names == ["便宜", "贵"]


@pytest.mark.asyncio
async def test_products_price_desc(client, db_session):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db_session.add(make_product("便宜", 20.0, created_at=base))
    db_session.add(make_product("贵", 90.0, created_at=base))
    await db_session.flush()
    res = await client.get("/api/v1/products?sort=price_desc")
    names = [p["name"] for p in res.json()["data"]["items"]]
    assert names == ["贵", "便宜"]
