"""AI 效果看板 API（管理员）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.order import Order
from app.models.knowledge import KnowledgeEntry
from app.models.product import Product, ProductStatus
from app.models.user import User, UserStatus
from app.schemas.common import APIResponse
from app.api.deps import require_role

router = APIRouter()


@router.get("/ai/overview", response_model=APIResponse[dict], summary="AI 效果概览")
async def ai_overview(
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    """返回 AI 相关的核心统计指标"""

    # 1. 对话相关订单数（含 ai_conversation_id 的订单）
    ai_order_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.ai_conversation_id.is_not(None))
    )
    ai_orders = ai_order_result.scalar() or 0

    # 2. 总订单数
    total_result = await db.execute(select(func.count()).select_from(Order))
    total_orders = total_result.scalar() or 0

    # 3. 商品总数
    product_result = await db.execute(
        select(func.count()).select_from(Product).where(Product.status == ProductStatus.ON_SALE)
    )
    total_products = product_result.scalar() or 0

    # 4. 知识库条目数
    kb_result = await db.execute(
        select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.status == "active")
    )
    kb_entries = kb_result.scalar() or 0

    # 5. 零售商总数
    user_result = await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)
    )
    active_users = user_result.scalar() or 0

    # 6. 转化率
    conversion_rate = round(ai_orders / total_orders * 100, 1) if total_orders > 0 else 0

    return APIResponse.ok(data={
        "total_orders": total_orders,
        "ai_orders": ai_orders,
        "conversion_rate": conversion_rate,
        "total_products": total_products,
        "kb_entries": kb_entries,
        "active_users": active_users,
    })


@router.get("/ai/trends", response_model=APIResponse[list[dict]], summary="AI 趋势数据")
async def ai_trends(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    """返回按日统计的订单量和AI对话订单量趋势"""
    trends = []
    now = datetime.now(timezone.utc)

    for i in range(days):
        day_start = (now - timedelta(days=days - 1 - i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # 当日总订单
        day_total = await db.execute(
            select(func.count()).select_from(Order).where(
                Order.created_at >= day_start, Order.created_at < day_end
            )
        )
        # 当日 AI 订单
        day_ai = await db.execute(
            select(func.count()).select_from(Order).where(
                Order.created_at >= day_start, Order.created_at < day_end,
                Order.ai_conversation_id.is_not(None)
            )
        )

        trends.append({
            "date": day_start.strftime("%m-%d"),
            "total": day_total.scalar() or 0,
            "ai": day_ai.scalar() or 0,
        })

    return APIResponse.ok(data=trends)


@router.get("/ai/model-usage", response_model=APIResponse[dict], summary="模型调用统计")
async def model_usage(
    _admin: dict = Depends(require_role("admin", "operator")),
):
    """返回模型使用统计（Phase 3: deepseek + qwen 路由分布）"""
    # 当前为简版 — 后续可接入 LLM 调用日志表
    return APIResponse.ok(data={
        "models": [
            {"name": "DeepSeek V4 Pro", "scenarios": ["对话下单", "意图识别", "知识RAG"], "status": "active"},
            {"name": "千问 qwen-max", "scenarios": ["商品推荐"], "status": "active"},
        ],
        "routing": {
            "chat": "deepseek",
            "recommend": "qwen",
            "rag": "deepseek",
            "intent": "deepseek",
        }
    })
