"""对话状态机 + 上下文管理"""
from enum import StrEnum
from dataclasses import dataclass, field
from datetime import datetime, timezone


class ConversationState(StrEnum):
    IDLE = "idle"
    RECOMMENDING = "recommending"
    BUILDING_ORDER = "building_order"
    CONFIRMING = "confirming"
    COMPLETED = "completed"


@dataclass
class ConversationContext:
    """单次对话的上下文（内存存储，后续升级 Redis）"""
    user_id: str
    state: ConversationState = ConversationState.IDLE
    history: list[dict] = field(default_factory=list)
    # 推荐上下文
    last_recommendations: list[dict] = field(default_factory=list)
    # 订单构建上下文
    selected_product: dict | None = None
    order_quantity: int = 0
    order_payment_method: str | None = None
    # 用户画像
    user_level: str = "normal"
    user_profile_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationManager:
    """管理所有活跃对话（内存存储）"""

    def __init__(self):
        self._conversations: dict[str, ConversationContext] = {}

    def get_or_create(self, user_id: str) -> ConversationContext:
        if user_id not in self._conversations:
            self._conversations[user_id] = ConversationContext(user_id=user_id)
        return self._conversations[user_id]

    def reset(self, user_id: str):
        self._conversations[user_id] = ConversationContext(user_id=user_id)

    def update(self, user_id: str, **kwargs):
        ctx = self.get_or_create(user_id)
        for key, value in kwargs.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)


conv_manager = ConversationManager()
