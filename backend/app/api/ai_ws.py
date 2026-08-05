"""AI WebSocket 端点"""
from fastapi import APIRouter, WebSocket, Query
from jose import jwt, JWTError
from app.config import get_settings
from app.ai.ws_handler import handle_chat

router = APIRouter()


@router.websocket("/ws/chat")
async def ai_chat_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    AI 对话 WebSocket 通道。需携带 JWT token 认证。

    消息格式（前端→后端）: {"content": "用户输入"}

    消息格式（后端→前端）:
    {"type": "text_chunk", "content": "..."}   ← 流式 token
    {"type": "text_done", "content": "..."}    ← 完整回复
    {"type": "thinking", "content": "..."}     ← 处理中
    {"type": "text", "content": "..."}         ← 纯文本
    {"type": "product_card", "products": [...]}  ← 商品卡片
    {"type": "order_confirm", "order": {...}}    ← 订单确认
    {"type": "order_result", "order": {...}}     ← 下单结果
    {"type": "quick_replies", "items": [...]}    ← 快捷回复
    {"type": "error", "content": "..."}          ← 错误
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Token 无效")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Token 无效或已过期")
        return

    user_context = {"user_id": user_id, "role": payload.get("role", "retailer")}
    await handle_chat(websocket, user_id, user_context)
