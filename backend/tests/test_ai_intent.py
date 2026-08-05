"""AI 相关测试"""
import pytest


def test_system_prompt_contains_brand():
    """验证 system prompt 包含品牌元素"""
    from app.ai.prompts.system import SYSTEM_PROMPT
    assert "小暖" in SYSTEM_PROMPT
    assert "儿童产品" in SYSTEM_PROMPT
    assert "游泳设备" in SYSTEM_PROMPT
    assert "护肤产品" in SYSTEM_PROMPT
    assert "健康产品" in SYSTEM_PROMPT
    assert "给孩子温柔的呵护" in SYSTEM_PROMPT


def test_system_prompt_contains_safety():
    """验证 system prompt 强调安全性"""
    from app.ai.prompts.system import SYSTEM_PROMPT
    assert "安全" in SYSTEM_PROMPT
    assert "认证" in SYSTEM_PROMPT


def test_llm_client_import():
    """验证 LLM 客户端可导入"""
    from app.ai.llm_client import get_llm_client, chat_stream, chat_sync
    assert callable(get_llm_client)
    assert callable(chat_sync)
    # chat_stream 是 async generator function（用 yield 的 async def）
    import inspect
    assert inspect.isasyncgenfunction(chat_stream)


@pytest.mark.asyncio
async def test_llm_chat_sync_mock():
    """测试非流式对话（mock API 调用）"""
    from unittest.mock import AsyncMock, patch
    from app.ai.llm_client import chat_sync

    with patch('app.ai.llm_client.AsyncOpenAI') as mock_openai:
        mock_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "你好，我是小暖！"
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_instance

        result = await chat_sync([{"role": "user", "content": "你好"}], model="deepseek")
        assert "小暖" in result


@pytest.mark.asyncio
async def test_llm_chat_stream_mock():
    """测试流式对话（mock API 调用）"""
    from unittest.mock import AsyncMock, patch, MagicMock
    from app.ai.llm_client import chat_stream

    with patch('app.ai.llm_client.AsyncOpenAI') as mock_openai:
        # 模拟流式返回
        class MockChoice:
            def __init__(self, content):
                self.delta = type('obj', (object,), {'content': content})()

        class MockChunk:
            def __init__(self, content):
                self.choices = [MockChoice(content)]

        chunks_data = ["你好", "，我是", "小暖"]

        # 创建 async iterable（用 AsyncMock 模拟 aiter/anext）
        mock_chunks = [MockChunk(c) for c in chunks_data]

        class _AsyncIter:
            def __init__(self, items):
                self._items = items
                self._idx = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._idx >= len(self._items):
                    raise StopAsyncIteration
                item = self._items[self._idx]
                self._idx += 1
                return item

        mock_stream = _AsyncIter(mock_chunks)

        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_stream)
        mock_openai.return_value = mock_instance

        chunks = []
        async for chunk in chat_stream([{"role": "user", "content": "你好"}], model="deepseek"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "你好，我是小暖"


def test_connection_manager():
    """测试连接管理器"""
    from app.ai.ws_handler import ConnectionManager
    manager = ConnectionManager()
    assert isinstance(manager.active_connections, dict)
    assert len(manager.active_connections) == 0


# ── P2-2 测试 ──

def test_intent_prompt_contains_all_types():
    """验证意图分类 prompt 包含所有意图类型"""
    from app.ai.intent import INTENT_PROMPT
    assert "recommend" in INTENT_PROMPT
    assert "search" in INTENT_PROMPT
    assert "order" in INTENT_PROMPT
    assert "negotiate" in INTENT_PROMPT
    assert "query" in INTENT_PROMPT
    assert "reorder" in INTENT_PROMPT
    assert "greeting" in INTENT_PROMPT


def test_intent_types_enum():
    """验证意图枚举值"""
    from app.ai.intent import IntentType
    assert IntentType.RECOMMEND == "recommend"
    assert IntentType.ORDER == "order"
    assert len(list(IntentType)) == 8


def test_conversation_state_machine():
    """验证对话状态机"""
    from app.ai.conversation import ConversationContext, ConversationState, conv_manager

    user_id = "test_p2_2_user"
    ctx = conv_manager.get_or_create(user_id)
    assert ctx.state == ConversationState.IDLE
    assert ctx.last_recommendations == []

    # 状态切换
    conv_manager.update(user_id, state=ConversationState.RECOMMENDING, last_recommendations=[{"id": "1", "name": "测试"}])
    ctx = conv_manager.get_or_create(user_id)
    assert ctx.state == ConversationState.RECOMMENDING
    assert len(ctx.last_recommendations) == 1

    # 重置
    conv_manager.reset(user_id)
    ctx = conv_manager.get_or_create(user_id)
    assert ctx.state == ConversationState.IDLE
    assert ctx.last_recommendations == []


def test_conversation_context_defaults():
    """验证对话上下文默认值"""
    from app.ai.conversation import ConversationContext
    ctx = ConversationContext(user_id="test")
    assert ctx.state == "idle"
    assert ctx.order_quantity == 0
    assert ctx.user_level == "normal"
    assert ctx.selected_product is None


@pytest.mark.asyncio
async def test_classify_intent_returns_valid_dict():
    """classify_intent 始终返回有效的字典结构（即使没有API key）"""
    import app.ai.intent as intent_module
    result = await intent_module.classify_intent("你好")
    assert isinstance(result, dict)
    for key in ("intent", "keywords", "quantity", "product_name"):
        assert key in result


@pytest.mark.asyncio
async def test_classify_intent_handles_various_inputs():
    """不同输入都应返回有效结构（不崩溃）"""
    import app.ai.intent as intent_module
    for user_input in ["推荐游泳圈", "100件", "你好", ""]:
        result = await intent_module.classify_intent(user_input)
        assert isinstance(result, dict)
        assert "intent" in result


@pytest.mark.asyncio
async def test_classify_intent_greeting_mock():
    """测试意图分类（mock LLM 返回 greeting）"""
    from unittest.mock import patch, AsyncMock
    import app.ai.intent as intent_module

    with patch.object(intent_module, "chat_sync", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = '{"intent":"greeting","keywords":[],"quantity":null,"product_name":null}'

        result = await intent_module.classify_intent("你好")
        assert result["intent"] == "greeting"


@pytest.mark.asyncio
async def test_classify_intent_recommend_mock():
    """测试意图分类（mock LLM 返回 recommend）"""
    from unittest.mock import patch, AsyncMock
    import app.ai.intent as intent_module

    with patch.object(intent_module, "chat_sync", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = '{"intent":"recommend","keywords":["swim","child"],"quantity":null,"product_name":null}'

        result = await intent_module.classify_intent("help me find children swim ring")
        assert result["intent"] == "recommend"
        assert "swim" in result["keywords"]


@pytest.mark.asyncio
async def test_classify_intent_fallback_on_error():
    """测试意图分类解析失败时的兜底"""
    from unittest.mock import patch, AsyncMock
    import app.ai.intent as intent_module

    with patch.object(intent_module, "chat_sync", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "invalid json {{{"

        result = await intent_module.classify_intent("随便说点什么")
        assert result["intent"] in (intent_module.IntentType.GREETING, intent_module.IntentType.UNKNOWN)
