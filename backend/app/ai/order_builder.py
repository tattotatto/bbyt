"""订单构建器：从对话上下文提取结构化订单并调用业务层创建"""
import uuid
import re
from decimal import Decimal
from app.ai.conversation import conv_manager, ConversationState


async def build_order_from_context(
    user_id: str,
    db_session_factory,
) -> dict:
    """
    从对话上下文中构建并创建订单。

    Returns:
        {"success": True, "order": {...}} 或 {"success": False, "error": "原因"}
    """
    ctx = conv_manager.get_or_create(user_id)

    if not ctx.selected_product:
        return {"success": False, "error": "还没有选择商品呢~ 请先告诉小暖您想要哪一款"}

    if ctx.order_quantity <= 0:
        return {"success": False, "error": "请告诉小暖您需要多少件~"}

    if db_session_factory is None:
        return {"success": False, "error": "数据库连接不可用"}

    product_id = ctx.selected_product.get("id", "")

    # 构建订单 items（order_service 会匹配定价）
    items = [{
        "product_id": product_id,
        "name": ctx.selected_product.get("name", ""),
        "qty": ctx.order_quantity,
        "unit_price": 0,  # 由 order_service.create_order 通过定价引擎计算
        "subtotal": 0,
    }]

    try:
        from app.services.order_service import create_order

        async with db_session_factory() as session:
            order = await create_order(
                db=session,
                retailer_id=uuid.UUID(user_id),
                items=items,
                payment_method=ctx.order_payment_method or "wechat_pay",
            )
            order_data = {
                "order_id": str(order.id),
                "order_no": order.order_no,
                "total_amount": order.total_amount,
                "items": order.items,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
            }
            # 更新对话状态为已完成
            conv_manager.update(str(user_id), state=ConversationState.COMPLETED)
            return {"success": True, "order": order_data}
    except ValueError as e:
        return {"success": False, "error": str(e)}


def parse_order_intent(user_input: str, ctx=None) -> dict:
    """
    从用户文本中提取订单意图（商品选择、数量、支付方式）。

    规则+正则混合：
    - "第X款" → product_index
    - "N件" → quantity
    - 微信/转账 → payment_method
    """
    result = {"product_index": None, "quantity": 0, "payment_method": None}

    # 匹配 "第X款" 或 "第X个"
    index_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*(款|个|种)", user_input)
    if index_match:
        num_str = index_match.group(1)
        num_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                   "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        result["product_index"] = num_map.get(num_str, int(num_str) if num_str.isdigit() else 1)

    # 匹配数量
    qty_match = re.search(r"(\d+)\s*件", user_input)
    if qty_match:
        result["quantity"] = int(qty_match.group(1))

    # 匹配支付方式
    if "微信" in user_input:
        result["payment_method"] = "wechat_pay"
    elif "转账" in user_input or "银行" in user_input:
        result["payment_method"] = "bank_transfer"

    return result
