"""A/B 测试：分流 + 简单统计"""
import hashlib
import json
from datetime import datetime, timezone

# 实验配置
EXPERIMENTS = {
    "ai_model": {
        "name": "AI 模型对比",
        "variants": ["deepseek", "qwen"],
        "traffic_split": [0.5, 0.5],  # 50/50分流
    },
}


def assign_variant(experiment_key: str, user_id: str) -> str:
    """为用户分配实验变体（基于user_id哈希，保证同一用户始终同一变体）"""
    config = EXPERIMENTS.get(experiment_key)
    if not config:
        return "default"
    h = int(hashlib.md5(f"{experiment_key}:{user_id}".encode()).hexdigest(), 16)
    ratio = (h % 100) / 100.0
    cumulative = 0
    for variant, split in zip(config["variants"], config["traffic_split"]):
        cumulative += split
        if ratio <= cumulative:
            return variant
    return config["variants"][-1]


def record_result(experiment_key: str, user_id: str, variant: str, success: bool):
    """记录实验结果（后续可存入DB）"""
    # Phase 4: 打印日志，后续可存表
    print(f"[AB] {experiment_key} | user={user_id} | variant={variant} | success={success}")
