"""种子脚本测试：幂等性与数据合法性。

每个用例都同时请求 `client` 和 `db_session` 两个 fixture —— 这不是多余的：
`db_session`（tests/conftest.py:78-83）只开一个 session，**不建表**；
真正跑 `Base.metadata.create_all` 的是 `client`（tests/conftest.py:56-58）。
现有测试无一例外都是 `(client, db_session)` 一起用，只写 `db_session`
会得到 `no such table: categories`。
"""
import pytest
from sqlalchemy import select, func

from scripts.seed import CATEGORIES, run_seed


async def _counts(db) -> dict[str, int]:
    from app.models.product import Category, Product
    from app.models.case import DesignCase
    from app.models.promotion import Promotion

    out = {}
    for name, model in (
        ("categories", Category),
        ("products", Product),
        ("cases", DesignCase),
        ("promotions", Promotion),
    ):
        out[name] = (await db.execute(select(func.count()).select_from(model))).scalar_one()
    return out


@pytest.mark.asyncio
async def test_seed_creates_data(client, db_session):
    written = await run_seed(db_session)
    await db_session.commit()

    counts = await _counts(db_session)
    assert counts["categories"] > 0
    assert counts["products"] > 0
    assert counts["cases"] > 0
    assert counts["promotions"] > 0
    assert sum(written.values()) > 0


@pytest.mark.asyncio
async def test_seed_is_idempotent(client, db_session):
    """空库连跑两遍不产生重复。"""
    await run_seed(db_session)
    await db_session.commit()
    first = await _counts(db_session)

    await run_seed(db_session)
    await db_session.commit()
    second = await _counts(db_session)

    assert first == second


@pytest.mark.asyncio
async def test_seed_is_idempotent_from_partial_state(client, db_session):
    """半有半无的中间状态：只建了分类，商品/案例/促销还没建。

    这才是幂等性的真实检验 —— 空库跑两遍很容易过，
    「分类在、商品不在」的状态最容易被「先查后插」写错。
    """
    from app.models.product import Category

    db_session.add(Category(name="婴童服饰", sort_order=1, status="active"))
    await db_session.commit()

    written = await run_seed(db_session)
    await db_session.commit()
    first = await _counts(db_session)

    # 种子里一级分类 + 全部子分类的总条数。从 CATEGORIES 算出来而不是写死，
    # 以后往种子里加分类，这条断言不会失效。
    expected_total = sum(1 + len(children) for _, _, children in CATEGORIES)

    # 预先存在的那条一级分类不能被重复插入 —— 这是本用例的核心
    dupes = (await db_session.execute(
        select(func.count()).select_from(Category).where(
            Category.name == "婴童服饰", Category.parent_id.is_(None)
        )
    )).scalar_one()
    assert dupes == 1, "预先存在的一级分类被重复插入了"

    # 总数 = 全部应建的条数（预置那条本来就在，所以总数不变）
    assert first["categories"] == expected_total
    # 其余三类照常建出来
    assert first["products"] > 0
    assert first["cases"] > 0
    assert first["promotions"] > 0
    # 新增只比全量少那一条预置的
    assert written["categories"] == expected_total - 1

    await run_seed(db_session)
    await db_session.commit()
    assert await _counts(db_session) == first


@pytest.mark.asyncio
async def test_seeded_products_are_well_formed(client, db_session):
    """每个种子商品都要是完整的：定价矩阵能被定价引擎用（qty 升序、有 normal 档），
    并且必须挂在分类下 —— 这条同时守住 PRODUCTS 里的分类名不会写错。
    """
    from app.models.product import Product

    await run_seed(db_session)
    await db_session.commit()

    products = (await db_session.execute(select(Product))).scalars().all()
    assert products, "没有种子商品"
    for p in products:
        assert p.category_id is not None, f"{p.name} 的 category_id 为空 —— PRODUCTS 里的分类名写错了吗？"
        assert "normal" in p.pricing_rules, f"{p.name} 缺 normal 档"
        for level, tiers in p.pricing_rules.items():
            assert tiers, f"{p.name}/{level} 是空档"
            qtys = [t["qty"] for t in tiers]
            assert qtys == sorted(qtys), f"{p.name}/{level} 的 qty 不是升序"
            for t in tiers:
                assert t["qty"] > 0 and t["price"] > 0, f"{p.name}/{level} 有非法阶梯"


@pytest.mark.asyncio
async def test_seeded_promotions_are_currently_active(client, db_session):
    """品牌活动分区取的是 /promotions/active，种子促销必须落在有效期内。"""
    from datetime import datetime, timezone
    from app.models.promotion import Promotion

    await run_seed(db_session)
    await db_session.commit()

    now = datetime.now(timezone.utc)
    promos = (await db_session.execute(select(Promotion))).scalars().all()
    assert promos
    for p in promos:
        assert p.is_active, f"{p.title} 没启用"
        assert p.start_time.replace(tzinfo=None) <= now.replace(tzinfo=None) <= p.end_time.replace(tzinfo=None), f"{p.title} 不在有效期内"
