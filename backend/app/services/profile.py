"""用户画像引擎：从订单历史计算多维度画像"""
import uuid
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import RetailerProfile

# 7个画像维度（spec 11.1）
DEFAULT_PROFILE = {
    "category_preference": {},     # {"category_id": weight, ...}
    "age_range_preference": {},    # {"3-6岁": 0.6, "0-3岁": 0.4}
    "price_band": {"min": 0, "max": 0, "avg": 0},
    "brand_preference": {},        # {"brand_name": count, ...}
    "purchase_cycle_days": 30,     # 预测采购周期（天）
    "quantity_preference": 0,      # 平均每单数量
    "seasonal_preference": {},     # {"游泳": [6,7,8], "护肤": [9,10,11], "健康": [1..12]}
    "last_updated": None,
}


async def compute_user_profile(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """计算用户画像（从历史已完成订单）"""
    # 1. 获取最近6个月的已完成订单
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    result = await db.execute(
        select(Order)
        .where(
            Order.retailer_id == user_id,
            Order.status == OrderStatus.COMPLETED,
            Order.created_at >= six_months_ago,
        )
        .order_by(Order.created_at.asc())
    )
    orders = result.scalars().all()

    if not orders:
        return {**DEFAULT_PROFILE, "last_updated": datetime.now(timezone.utc).isoformat()}

    # 2. 计算品类偏好（按购买次数加权）
    category_counter = Counter()
    age_range_counter = Counter()
    brand_counter = Counter()
    all_prices = []
    all_quantities = []
    seasonal_map = defaultdict(list)
    order_dates = []

    for order in orders:
        order_dates.append(order.created_at)
        for item in (order.items or []):
            # 品类偏好（通过 product_id 反查品类）
            pid_str = item.get("product_id")
            if pid_str:
                try:
                    pid = uuid.UUID(pid_str)
                except (ValueError, AttributeError):
                    pid = None
            else:
                pid = None
            product = None
            if pid:
                product_result = await db.execute(
                    select(Product).where(Product.id == pid)
                )
                product = product_result.scalar_one_or_none()
            if product:
                cat_id = str(product.category_id) if product.category_id else "unknown"
                category_counter[cat_id] += item.get("qty", 1)
                if product.age_range:
                    age_range_counter[product.age_range] += item.get("qty", 1)

            all_prices.append(item.get("unit_price", 0))
            all_quantities.append(item.get("qty", 0))

            # 季节性：按商品名关键词
            name = item.get("name", "")
            if "游泳" in name:
                seasonal_map["游泳"].append(order.created_at.month)
            elif "护肤" in name or "防晒" in name:
                seasonal_map["护肤"].append(order.created_at.month)
            elif "健康" in name or "维生素" in name:
                seasonal_map["健康"].append(order.created_at.month)

    # 3. 计算采购周期（相邻订单平均间隔天数）
    purchase_cycle = 30  # 默认
    if len(order_dates) >= 2:
        intervals = [
            (order_dates[i + 1] - order_dates[i]).days
            for i in range(len(order_dates) - 1)
        ]
        intervals = [d for d in intervals if d > 0]
        if intervals:
            purchase_cycle = int(sum(intervals) / len(intervals))

    # 4. 构建画像
    total_qty = sum(category_counter.values()) or 1
    profile = {
        "category_preference": {
            k: round(v / total_qty, 2) for k, v in category_counter.most_common(10)
        },
        "age_range_preference": dict(age_range_counter.most_common(5)),
        "price_band": {
            "min": min(all_prices) if all_prices else 0,
            "max": max(all_prices) if all_prices else 0,
            "avg": round(sum(all_prices) / len(all_prices), 2) if all_prices else 0,
        },
        "brand_preference": dict(brand_counter.most_common(10)),
        "purchase_cycle_days": purchase_cycle,
        "quantity_preference": (
            int(sum(all_quantities) / len(all_quantities)) if all_quantities else 0
        ),
        "seasonal_preference": {k: list(set(v)) for k, v in seasonal_map.items()},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return profile


async def save_profile(user_id: uuid.UUID, profile: dict, db: AsyncSession):
    """将画像保存到 retailer_profiles"""
    result = await db.execute(
        select(RetailerProfile).where(RetailerProfile.user_id == user_id)
    )
    rp = result.scalar_one_or_none()
    if rp:
        rp.purchase_history_summary = profile
        await db.flush()


async def update_profile_async(user_id: uuid.UUID, db_session_factory):
    """异步更新用户画像（供 Redis Pub/Sub 触发调用）"""
    async with db_session_factory() as session:
        profile = await compute_user_profile(user_id, session)
        await save_profile(user_id, profile, session)
        await session.commit()


def get_profile_for_ai(user_profile: dict | None) -> str:
    """将画像格式化为 AI 对话可用的用户摘要文本"""
    if not user_profile:
        return ""
    parts = []
    cats = user_profile.get("category_preference", {})
    if cats:
        top_cat = max(cats, key=cats.get) if cats else ""
        parts.append(f"偏好品类: {top_cat}")
    age = user_profile.get("age_range_preference", {})
    if age:
        top_age = max(age, key=age.get) if age else ""
        parts.append(f"偏好适龄段: {top_age}")
    cycle = user_profile.get("purchase_cycle_days", 0)
    if cycle:
        parts.append(f"采购周期约{cycle}天")
    parts.append(f"平均每单{user_profile.get('quantity_preference', 0)}件")
    return "；".join(parts)
