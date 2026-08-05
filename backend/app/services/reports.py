"""AI 采购分析报表"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderStatus
from app.ai.llm_client import chat_sync


async def generate_purchase_report(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """生成零售商的采购分析报告"""
    # 获取最近3个月订单
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
    result = await db.execute(
        select(Order).where(
            Order.retailer_id == user_id,
            Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CONFIRMED]),
            Order.created_at >= three_months_ago,
        ).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    if not orders:
        return {"summary": "暂无足够数据生成报告", "order_count": 0, "total_spent": 0}

    # 基础统计
    total_spent = sum(o.total_amount for o in orders)
    order_count = len(orders)
    avg_order = total_spent // order_count if order_count else 0

    # 品类分布
    category_spend = {}
    all_products = []
    for order in orders:
        for item in (order.items or []):
            name = item.get("name", "")
            qty = item.get("qty", 0)
            subtotal = item.get("subtotal", 0)
            all_products.append({"name": name, "qty": qty, "subtotal": subtotal})
            # 简单按商品名首词归类
            cat = name[:4] if name else "其他"
            category_spend[cat] = category_spend.get(cat, 0) + subtotal

    # Top 品类
    top_categories = sorted(category_spend.items(), key=lambda x: x[1], reverse=True)[:3]

    # 采购趋势（按月）
    monthly = {}
    for order in orders:
        if order.created_at:
            month_key = order.created_at.strftime("%Y-%m")
            monthly[month_key] = monthly.get(month_key, 0) + order.total_amount

    # 生成 AI 总结
    summary_prompt = f"""根据以下零售商采购数据，生成一段100字以内的采购分析摘要：
- 近3个月采购{order_count}次，总金额¥{total_spent/100:.0f}
- 月均采购{monthly.values() and sum(monthly.values())/len(monthly)/100:.0f}元
- 偏好品类：{', '.join([f'{c}(¥{v/100:.0f})' for c,v in top_categories])}
请用"小暖"的口吻（温柔专业），给出1-2条采购优化建议。"""

    try:
        ai_summary = await chat_sync(
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7, max_tokens=200,
        )
    except Exception:
        ai_summary = "采购数据已汇总，请查看下方详细统计。"

    return {
        "summary": ai_summary,
        "order_count": order_count,
        "total_spent": total_spent,
        "avg_order": avg_order,
        "top_categories": [{"name": c, "amount": v} for c, v in top_categories],
        "monthly_trend": [{"month": k, "amount": v} for k, v in sorted(monthly.items())],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
