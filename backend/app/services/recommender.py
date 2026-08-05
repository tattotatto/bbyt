"""推荐引擎：基于用户画像的商品推荐"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product, ProductStatus
from app.models.user import RetailerProfile
from app.services.profile import compute_user_profile, get_profile_for_ai
from app.services.pricing import get_price_range


async def get_homepage_recommendations(user_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
    """首页推荐：基于用户品类偏好 + 季节性"""
    # 1. 加载画像
    result = await db.execute(
        select(RetailerProfile).where(RetailerProfile.user_id == user_id)
    )
    rp = result.scalar_one_or_none()
    profile = rp.purchase_history_summary if rp and rp.purchase_history_summary else None

    # 2. 获取在售商品
    from datetime import datetime, timezone
    current_month = datetime.now(timezone.utc).month

    product_result = await db.execute(
        select(Product).where(Product.status == ProductStatus.ON_SALE).limit(50)
    )
    products = product_result.scalars().all()

    # 3. 按画像排序
    scored = []
    for p in products:
        score = 0
        if profile:
            cat_id = str(p.category_id) if p.category_id else ""
            cat_weight = profile.get("category_preference", {}).get(cat_id, 0)
            score += cat_weight * 10  # 品类匹配加分

            age_range = p.age_range or ""
            age_weight = profile.get("age_range_preference", {}).get(age_range, 0)
            score += age_weight * 3  # 适龄匹配加分

            # 季节性加分
            seasonal = profile.get("seasonal_preference", {})
            for season_name, months in seasonal.items():
                if current_month in months and season_name in p.name:
                    score += 5

        scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "image": p.images[0] if p.images else "",
            "age_range": p.age_range,
            "price_min": get_price_range(p.pricing_rules)[0],
            "price_max": get_price_range(p.pricing_rules)[1],
            "stock": p.stock,
            "safety_certifications": p.safety_certifications or [],
        }
        for p, score in scored[:limit]
    ]


async def get_restock_suggestions(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """补货建议：根据采购周期预测"""
    from datetime import datetime, timezone, timedelta

    result = await db.execute(
        select(RetailerProfile).where(RetailerProfile.user_id == user_id)
    )
    rp = result.scalar_one_or_none()
    profile = rp.purchase_history_summary if rp and rp.purchase_history_summary else None

    if not profile:
        return []

    cycle_days = profile.get("purchase_cycle_days", 30)

    # 查找超过采购周期未补货的品类
    from app.models.order import Order, OrderStatus
    cutoff = datetime.now(timezone.utc) - timedelta(days=cycle_days)
    order_result = await db.execute(
        select(Order).where(
            Order.retailer_id == user_id,
            Order.status == OrderStatus.COMPLETED,
            Order.created_at < cutoff,
        ).order_by(Order.created_at.desc()).limit(5)
    )
    old_orders = order_result.scalars().all()

    suggestions = []
    seen_products = set()
    for order in old_orders:
        for item in (order.items or []):
            pid = item.get("product_id", "")
            if pid and pid not in seen_products:
                seen_products.add(pid)
                suggestions.append({
                    "product_name": item.get("name", ""),
                    "last_qty": item.get("qty", 0),
                    "last_order_date": order.created_at.isoformat() if order.created_at else "",
                    "suggested_qty": int(item.get("qty", 0) * 1.2),  # 建议增加20%
                })

    return suggestions[:5]
