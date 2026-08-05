"""促销价格计算"""
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.promotion import Promotion, PromotionType


async def get_active_promotions(db, product_id: str | None = None):
    """获取当前活跃的促销活动"""
    now = datetime.now(timezone.utc)
    query = select(Promotion).where(
        Promotion.is_active == True,
        Promotion.start_time <= now,
        Promotion.end_time >= now,
    )
    result = await db.execute(query)
    all_promos = result.scalars().all()
    return [
        p for p in all_promos
        if p.product_ids is None or product_id in p.product_ids
    ]


def apply_promotion(total_amount: int, promotion) -> int:
    """计算应用促销后的金额(分)"""
    if promotion.type == PromotionType.FULL_REDUCTION:
        threshold = promotion.rules.get("threshold", 0)
        reduce = promotion.rules.get("reduce", 0)
        if total_amount >= threshold:
            return total_amount - reduce
    elif promotion.type == PromotionType.DISCOUNT:
        rate = promotion.rules.get("rate", 1.0)
        return int(total_amount * rate)
    return total_amount
