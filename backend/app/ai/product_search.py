"""为 AI 对话搜索商品"""
from sqlalchemy import select, or_
from app.models.product import Product, ProductStatus
from app.services.pricing import get_price_range


async def search_products_for_ai(db_session_factory, keywords: list[str], limit: int = 3) -> list[dict]:
    """搜索在售商品，返回 AI 对话用的简化格式"""
    async with db_session_factory() as session:
        conditions = []
        for kw in keywords:
            conditions.append(Product.name.ilike(f"%{kw}%"))
            conditions.append(Product.description.ilike(f"%{kw}%"))

        result = await session.execute(
            select(Product)
            .where(Product.status == ProductStatus.ON_SALE, or_(*conditions))
            .limit(limit)
        )
        products = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "name": p.name,
                "image": p.images[0] if p.images else "",
                "age_range": p.age_range,
                "safety_certifications": p.safety_certifications or [],
                "price_min": get_price_range(p.pricing_rules)[0],
                "price_max": get_price_range(p.pricing_rules)[1],
                "stock": p.stock,
                "min_order_qty": p.min_order_qty,
            }
            for p in products
        ]
