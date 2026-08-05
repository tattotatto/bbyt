"""WebSocket 连接管理器 + 消息路由"""
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.ai.llm_client import chat_stream
from app.ai.prompts.system import SYSTEM_PROMPT


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_json(self, user_id: str, data: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


async def handle_chat(websocket: WebSocket, user_id: str, user_context: dict):
    """
    主聊天处理循环：
    1. 发欢迎消息
    2. 接收用户文本
    3. 构建消息列表（system + 历史 + 当前）
    4. 流式调用 LLM
    5. 每个 token 推送给前端
    """
    await manager.connect(user_id, websocket)
    history: list[dict] = []

    # 启动心跳任务
    async def heartbeat():
        while user_id in manager.active_connections:
            await asyncio.sleep(30)
            try:
                await manager.send_json(user_id, {"type": "ping"})
            except Exception:
                break
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        # 1. 欢迎消息
        await manager.send_json(user_id, {
            "type": "text",
            "content": "您好！我是小暖，您的儿童产品选品助手。今天想了解哪类产品呢？😊",
        })
        await manager.send_json(user_id, {
            "type": "quick_replies",
            "items": ["游泳设备", "护肤产品", "健康产品", "查看新品"],
        })

        while True:
            # 2. 接收消息
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            user_input = msg.get("content", "").strip()
            if not user_input:
                continue

            # 3. 构建上下文
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history[-20:])
            messages.append({"role": "user", "content": user_input})

            # 4. thinking 提示
            await manager.send_json(user_id, {"type": "thinking", "content": "小暖正在思考..."})

            # 5. 流式输出
            full_response = ""
            async for token in chat_stream(messages, model="deepseek"):
                full_response += token
                await manager.send_json(user_id, {"type": "text_chunk", "content": token})

            # 6. 发送完成标记
            await manager.send_json(user_id, {"type": "text_done", "content": full_response})

            # 7. 记录历史（保留最近10轮=20条）
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": full_response})
            if len(history) > 20:
                history = history[-20:]

            # 8. 处理"确认下单"
            from app.ai.conversation import conv_manager, ConversationState

            ctx = conv_manager.get_or_create(user_id)

            if ("确认下单" in user_input or "confirm" in user_input.lower()) and ctx.state == ConversationState.BUILDING_ORDER:
                from app.ai.order_builder import build_order_from_context
                from app.database import async_session_factory

                result = await build_order_from_context(str(user_id), async_session_factory)
                if result["success"]:
                    await manager.send_json(user_id, {
                        "type": "order_result",
                        "order": result["order"],
                    })
                    await manager.send_json(user_id, {
                        "type": "text",
                        "content": f"订单已生成！订单号：{result['order']['order_no']}，总金额 ¥{result['order']['total_amount']/100:.2f}。您可以在「我的订单」中查看详情。",
                    })
                else:
                    await manager.send_json(user_id, {
                        "type": "text",
                        "content": f"抱歉~ {result['error']}",
                    })
                continue  # 跳过后续意图处理

            # 9. 意图识别 + 结构化回复
            from app.ai.intent import classify_intent, IntentType

            intent_result = await classify_intent(user_input)
            intent = intent_result.get("intent", IntentType.UNKNOWN)

            if intent in (IntentType.RECOMMEND, IntentType.SEARCH):
                ctx.state = ConversationState.RECOMMENDING
                keywords = intent_result.get("keywords", [user_input])
                from app.ai.product_search import search_products_for_ai
                from app.database import async_session_factory
                products = await search_products_for_ai(async_session_factory, keywords)
                if products:
                    ctx.last_recommendations = products
                    await manager.send_json(user_id, {
                        "type": "product_card",
                        "products": products,
                        "message": f"为您找到 {len(products)} 款相关商品：",
                    })
                    await manager.send_json(user_id, {
                        "type": "quick_replies",
                        "items": ["第一款", "第二款", "第三款", "再看看别的"],
                    })

            elif intent == IntentType.GREETING:
                ctx.state = ConversationState.IDLE
                # 问候已在流式回复中处理，这里可以追加快捷回复
                await manager.send_json(user_id, {
                    "type": "quick_replies",
                    "items": ["游泳设备", "护肤产品", "健康产品", "今日推荐"],
                })

            elif intent == IntentType.QUERY:
                # RAG 检索知识库 → 注入 LLM 上下文重新生成回复
                from app.ai.knowledge.engine import search_knowledge, format_rag_context
                from app.database import async_session_factory

                async with async_session_factory() as session:
                    rag_results = await search_knowledge(
                        db=session,
                        query_text=user_input,
                        top_k=3,
                    )
                    if rag_results:
                        rag_ctx = format_rag_context(rag_results)
                        # 重新调用 LLM，注入知识库上下文
                        await manager.send_json(user_id, {"type": "thinking", "content": "小暖正在查找相关资料..."})
                        rag_messages = messages + [{"role": "system", "content": f"补充知识：{rag_ctx}"}]
                        full_response = ""
                        async for token in chat_stream(rag_messages, model="deepseek"):
                            full_response += token
                            await manager.send_json(user_id, {"type": "text_chunk", "content": token})
                        await manager.send_json(user_id, {"type": "text_done", "content": full_response})
                        history.append({"role": "user", "content": user_input})
                        history.append({"role": "assistant", "content": full_response})

            elif intent == IntentType.ORDER or "下单" in user_input:
                from app.ai.order_builder import parse_order_intent

                ctx.state = ConversationState.BUILDING_ORDER
                order_info = parse_order_intent(user_input, ctx)

                if order_info["product_index"] and ctx.last_recommendations:
                    idx = order_info["product_index"] - 1
                    if 0 <= idx < len(ctx.last_recommendations):
                        ctx.selected_product = ctx.last_recommendations[idx]

                if order_info["quantity"]:
                    ctx.order_quantity = order_info["quantity"]
                if order_info["payment_method"]:
                    ctx.order_payment_method = order_info["payment_method"]

                if ctx.selected_product and ctx.order_quantity > 0:
                    await manager.send_json(user_id, {
                        "type": "order_confirm",
                        "order": {
                            "product": ctx.selected_product,
                            "quantity": ctx.order_quantity,
                            "payment_method": ctx.order_payment_method or "wechat_pay",
                        }
                    })
                    await manager.send_json(user_id, {
                        "type": "quick_replies",
                        "items": ["确认下单", "修改数量", "取消"],
                    })
                else:
                    await manager.send_json(user_id, {
                        "type": "text",
                        "content": "好的，请告诉小暖您要哪一款？需要多少件呢？",
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await manager.send_json(user_id, {"type": "error", "content": f"出错了：{str(e)}"})
        manager.disconnect(user_id)
    finally:
        heartbeat_task.cancel()
