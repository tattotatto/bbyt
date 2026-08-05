"""意图识别器：用 LLM 进行意图分类"""
from enum import StrEnum
from app.ai.llm_client import chat_sync


class IntentType(StrEnum):
    RECOMMEND = "recommend"
    SEARCH = "search"
    ORDER = "order"
    NEGOTIATE = "negotiate"
    QUERY = "query"
    REORDER = "reorder"
    GREETING = "greeting"
    UNKNOWN = "unknown"


INTENT_PROMPT = """你是一个意图分类器。分析用户在B2B儿童产品批发商城的输入，返回JSON格式的意图分类。

意图类型：
- recommend: 用户想要推荐商品（如"帮我推荐游泳圈"）
- search: 用户在搜索特定商品（如"有没有XX品牌"）
- order: 用户想下单购买（如"第一款拿100件"、"下单"）
- negotiate: 用户想协商价格或数量（如"100件能便宜吗"）
- query: 用户在查询信息（如"这款是什么材质的"、"上次的订单发了吗"）
- reorder: 用户想重复之前的订单（如"照上次的再来一份"）
- greeting: 问候或闲聊（如"你好"、"早上好"）
- unknown: 无法判断

请只返回JSON，格式：{{"intent":"recommend","keywords":["游泳","儿童"],"quantity":null,"product_name":null}}

用户输入：{user_input}"""


async def classify_intent(user_input: str) -> dict:
    """用 LLM 进行意图分类，返回结构化结果 {"intent":"...","keywords":[...],...}"""
    import json
    try:
        result = await chat_sync(
            messages=[{"role": "user", "content": INTENT_PROMPT.format(user_input=user_input)}],
            temperature=0.1,
            max_tokens=200,
        )
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception:
        return {"intent": IntentType.GREETING, "keywords": [], "quantity": None, "product_name": None}
