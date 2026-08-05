"""模型路由策略：根据场景选择最优模型 + 故障降级"""
from app.config import get_settings

settings = get_settings()

# 场景→模型映射（可通过配置文件/管理后台修改）
ROUTING = {
    "chat": "deepseek",         # 对话下单 → DeepSeek（逻辑推理强）
    "recommend": "qwen",        # 商品推荐 → 千问（中文语义细腻）
    "rag": "deepseek",          # 知识RAG → DeepSeek
    "intent": "deepseek",       # 意图识别 → DeepSeek
}

FAILOVER_CHAIN = ["deepseek", "qwen"]  # 降级链


def route_model(scenario: str) -> str:
    """根据场景选择模型，返回模型标识"""
    return ROUTING.get(scenario, settings.AI_DEFAULT_MODEL)


def get_failover_model(failed_model: str) -> str | None:
    """获取降级模型"""
    try:
        idx = FAILOVER_CHAIN.index(failed_model)
        if idx + 1 < len(FAILOVER_CHAIN):
            return FAILOVER_CHAIN[idx + 1]
    except ValueError:
        pass
    return None
