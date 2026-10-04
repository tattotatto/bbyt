"""种子数据：分类、商品、案例、促销。

幂等 —— 所有写入都走 _get_or_create（按业务唯一键查询，存在即返回）。
重复执行不产生重复行，也不覆盖运维后续手工改过的数据。
不用「先删后插」：那会抹掉人工修改。

用法：
    cd backend && python -m scripts.seed
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models.case import DesignCase
from app.models.product import Category, Product, ProductStatus
from app.models.promotion import Promotion, PromotionType


# ── 数据定义 ─────────────────────────────────────────────────────────────────

# (名称, 排序, 子分类)
CATEGORIES: list[tuple[str, int, list[str]]] = [
    ("婴童服饰", 1, ["连体衣", "外出服", "内衣套装"]),
    ("喂养用品", 2, ["奶瓶奶嘴", "辅食餐具", "消毒烘干"]),
    ("寝居出行", 3, ["婴儿床", "推车安全座椅", "床品寝具"]),
    ("洗护用品", 4, ["洗浴护理", "纸尿裤", "湿巾"]),
    ("玩具早教", 5, ["益智积木", "早教绘本", "户外玩具"]),
]

# 定价矩阵的键是小写等级值 normal/silver/gold（app/services/pricing.py:11）
def _tiers(base: float, min_qty: int = 10) -> dict:
    """按起批量生成三档等级价：等级越高单价越低，数量越大单价越低。"""
    return {
        "normal": [
            {"qty": min_qty, "price": round(base, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.94, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.88, 2)},
        ],
        "silver": [
            {"qty": min_qty, "price": round(base * 0.92, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.86, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.80, 2)},
        ],
        "gold": [
            {"qty": min_qty, "price": round(base * 0.85, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.79, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.72, 2)},
        ],
    }


# (分类名, 商品名, 适龄, 起批量, 基准价, 库存, 描述)
PRODUCTS: list[tuple[str, str, str, int, float, int, str]] = [
    ("连体衣", "纯棉长袖连体衣 新生儿爬服", "0-3岁", 10, 38.0, 5000, "精梳棉，四季通用，A 类婴幼儿标准"),
    ("连体衣", "冬季加厚夹棉连体衣", "0-3岁", 10, 68.0, 3000, "三层夹棉，保暖透气，包脚设计"),
    ("外出服", "婴儿外出抱衣套装", "0-3岁", 10, 88.0, 2000, "帽子+抱衣两件套，防风面料"),
    ("内衣套装", "儿童纯棉家居服两件套", "3-6岁", 20, 45.0, 4000, "40 支精梳棉，无骨缝制"),
    ("奶瓶奶嘴", "宽口径玻璃奶瓶 240ml", "0-3岁", 12, 42.0, 2600, "耐高温硼硅玻璃，防胀气奶嘴"),
    ("辅食餐具", "硅胶辅食碗勺套装", "0-3岁", 24, 16.0, 8000, "食品级硅胶，可蒸煮消毒"),
    ("消毒烘干", "紫外线奶瓶消毒柜", "0-3岁", 5, 320.0, 600, "18L，烘干+消毒二合一"),
    ("婴儿床", "实木多功能婴儿床", "0-3岁", 3, 260.0, 400, "新西兰松木，可改书桌，含护栏"),
    ("床品寝具", "婴儿床品七件套", "0-3岁", 10, 128.0, 1200, "A 类纯棉，含被芯枕芯床围"),
    ("推车安全座椅", "轻便折叠婴儿推车", "0-3岁", 4, 380.0, 300, "5.9kg 轻量，一键收车，可登机"),
    ("洗浴护理", "婴儿洗发沐浴二合一 500ml", "0-3岁", 24, 22.0, 6000, "无泪配方，弱酸性"),
    ("纸尿裤", "超薄透气纸尿裤 L 码", "0-3岁", 30, 58.0, 9000, "进口芯体，3 秒吸收"),
    ("湿巾", "婴儿手口湿巾 80 抽", "0-3岁", 60, 8.5, 20000, "纯水配方，无香精酒精"),
    ("益智积木", "大颗粒益智积木 80 粒", "3-6岁", 20, 52.0, 2500, "食品级 ABS，圆角无毛刺"),
    ("早教绘本", "启蒙认知绘本套装 20 册", "3-6岁", 30, 36.0, 3000, "硬壳撕不烂，环保大豆油墨"),
    ("户外玩具", "儿童三轮脚踏车", "3-6岁", 6, 168.0, 800, "加宽静音轮，可推可骑"),
]

# (标题, 描述, 分类标签, 风格标签, 面积, 排序, 精选)
CASES: list[tuple[str, str, list[str], list[str], str, int, bool]] = [
    ("北欧风儿童房整体方案", "0-3 岁婴幼儿房，含 12 件套柜体与睡眠区动线",
     ["儿童房"], ["ins风", "自然原木"], "50-100㎡", 100, True),
    ("蒙氏游戏区动线设计", "1-3 岁低龄安全动线，地面软包与低位收纳",
     ["游戏区"], ["ins风", "卡通童趣"], "50-100㎡", 90, True),
    ("连锁母婴生活馆标准店", "200㎡ 标准店型，商品区与体验区分区陈列",
     ["母婴生活馆"], ["简约现代"], "200㎡+", 80, True),
    ("婴童游泳馆空间方案", "恒温泳池区 + 家长等候区 + 更衣动线",
     ["婴童游泳馆"], ["简约现代"], "100-200㎡", 70, True),
    ("童趣儿童乐园主题店", "3-6 岁攀爬区与角色扮演区，全套软包防护",
     ["儿童乐园"], ["卡通童趣"], "200㎡+", 60, False),
    ("自然原木系亲子空间", "原木家具 + 绿植，亲子阅读与手作区",
     ["儿童房"], ["自然原木"], "50-100㎡", 50, False),
    ("社区母婴店改造案例", "80㎡ 老店翻新，动线重排后陈列面增加 40%",
     ["母婴生活馆"], ["简约现代"], "50-100㎡", 40, False),
    ("托育中心活动区设计", "分龄活动区 + 午睡区 + 配餐区一体化",
     ["儿童乐园"], ["ins风", "自然原木"], "200㎡+", 30, False),
]

# (标题, 类型, 规则)
PROMOTIONS: list[tuple[str, PromotionType, dict]] = [
    ("春季订货会 · 全场满减", PromotionType.FULL_REDUCTION,
     {"threshold": 500000, "reduce": 80000}),   # 满 5000 减 800（分）
    ("奶粉纸尿裤专享折扣", PromotionType.DISCOUNT,
     {"rate": 0.85}),                            # 85 折
    ("新品首发 · 连体衣限时价", PromotionType.FLASH_SALE,
     {"price": 3200, "limit_qty": 500}),         # 32 元 / 限 500 件
]


# ── 幂等写入 ─────────────────────────────────────────────────────────────────

async def _get_or_create_category(db, name: str, parent_id, sort_order: int) -> tuple[Category, bool]:
    stmt = select(Category).where(Category.name == name, Category.parent_id == parent_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing, False
    cat = Category(name=name, parent_id=parent_id, sort_order=sort_order, status="active")
    db.add(cat)
    await db.flush()
    return cat, True


async def _get_or_create_product(db, data: dict) -> bool:
    existing = (await db.execute(
        select(Product).where(Product.name == data["name"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(Product(**data))
    await db.flush()
    return True


async def _get_or_create_case(db, data: dict) -> bool:
    existing = (await db.execute(
        select(DesignCase).where(DesignCase.title == data["title"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(DesignCase(**data))
    await db.flush()
    return True


async def _get_or_create_promotion(db, data: dict) -> bool:
    existing = (await db.execute(
        select(Promotion).where(Promotion.title == data["title"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(Promotion(**data))
    await db.flush()
    return True


async def run_seed(db) -> dict[str, int]:
    """写入种子数据，返回各类新增条数。已存在的一律跳过。"""
    written = {"categories": 0, "products": 0, "cases": 0, "promotions": 0}

    # 分类：一级 + 子分类，商品挂在子分类下
    leaf_ids: dict[str, object] = {}
    for idx, (top_name, sort_order, children) in enumerate(CATEGORIES, start=1):
        top, created = await _get_or_create_category(db, top_name, None, sort_order * 10)
        written["categories"] += int(created)

        for c_idx, child_name in enumerate(children, start=1):
            child, child_created = await _get_or_create_category(
                db, child_name, top.id, c_idx
            )
            written["categories"] += int(child_created)
            leaf_ids[child_name] = child.id

    # 商品
    for cat_name, name, age_range, min_qty, base_price, stock, description in PRODUCTS:
        created = await _get_or_create_product(db, {
            "category_id": leaf_ids.get(cat_name),
            "name": name,
            "images": [],
            "description": description,
            "specs": {"适龄": age_range, "起批量": f"{min_qty} 件"},
            "age_range": age_range,
            "safety_certifications": [{"name": "3C认证", "icon": ""}],
            "is_virtual": False,
            "sales_count": 0,
            "stock": stock,
            "min_order_qty": min_qty,
            "pricing_rules": _tiers(base_price, min_qty),
            "status": ProductStatus.ON_SALE,
        })
        written["products"] += int(created)

    # 案例（images 留空：暂无真实案例图，前端用品牌色几何底纹兜底）
    for title, description, category_tags, style_tags, area, sort_order, featured in CASES:
        created = await _get_or_create_case(db, {
            "title": title,
            "description": description,
            "images": [],
            "category_tags": category_tags,
            "style_tags": style_tags,
            "store_area_range": area,
            "sort_order": sort_order,
            "is_featured": featured,
            "status": "published",
        })
        written["cases"] += int(created)

    # 促销：有效期落在「现在」前后，保证 /promotions/active 取得到
    now = datetime.now(timezone.utc)
    window = {"start_time": now - timedelta(days=7), "end_time": now + timedelta(days=180)}
    for title, ptype, rules in PROMOTIONS:
        created = await _get_or_create_promotion(db, {
            "title": title,
            "type": ptype,
            "rules": rules,
            "product_ids": None,
            "is_active": True,
            **window,
        })
        written["promotions"] += int(created)

    return written


async def main() -> None:
    async with async_session_factory() as db:
        written = await run_seed(db)
        await db.commit()
    print("种子数据完成，新增：", written)
    total = sum(written.values())
    if total == 0:
        print("（全部已存在，本次没有新增 —— 幂等生效）")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
