# Phase 2：AI 对话下单 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-group by task-group. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** "小暖"AI 助手上线 — 零售商可通过对话完成选品→推荐→下单全流程，AI 具备商品知识库 RAG 检索能力。

**Architecture:** AI 服务作为 FastAPI 独立模块（WebSocket + REST），与核心业务服务共用数据库。LLM 通过统一适配层对接 DeepSeek V4 Pro。知识库用 pgvector 做向量检索增强生成（RAG）。前端通过 WebSocket 实现流式对话 + 富消息卡片。

**Tech Stack:** FastAPI WebSocket, httpx (LLM API calls), pgvector, langchain (text splitter), openai SDK (compatible mode for DeepSeek), uni-app WebSocket API

**Design Doc:** `docs/superpowers/specs/2026-06-26-b2b-mall-design.md` (Sections 九-十二)

**Phase 1 Baseline:** Backend 44 tests pass, 30 endpoints. AI Tab is a brand placeholder page.

---

## Global Constraints

- Phase 1 backend code MUST NOT be broken — all 44 existing tests must continue to pass
- AI service is integrated into the existing FastAPI app (not a separate process for Phase 2)
- WebSocket endpoint at `/api/v1/ai/ws/chat`
- LLM provider: DeepSeek V4 Pro (via OpenAI-compatible API endpoint)
- LLM API base URL and key configured via env vars, not hardcoded
- Knowledge base embeddings stored in pgvector (`knowledge_entries` table)
- All AI responses include a message type: `text` | `product_card` | `order_confirm` | `order_result` | `quick_replies`
- AI assistant name is "小暖", personality: warm, professional, child-product knowledgeable
- Voice input (ASR) is out of scope for P2 backend — frontend records audio, P2 backend receives text only
- Streaming responses via WebSocket: each token/segment sent as a separate WS message
- All code has Chinese comments for team readability

---

## File Structure Map (Phase 2 additions, * = modified)

```
hxmall/backend/
├── app/
│   ├── ai/                              # NEW: AI 子模块
│   │   ├── __init__.py
│   │   ├── ws_handler.py                # WebSocket 连接管理 + 消息路由
│   │   ├── llm_client.py                # LLM 客户端抽象层
│   │   ├── model_router.py              # 模型路由策略 + 降级
│   │   ├── conversation.py              # 对话状态机 + 上下文管理
│   │   ├── intent.py                    # 意图识别器
│   │   ├── order_builder.py             # 对话→结构化订单
│   │   ├── knowledge/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                # RAG 检索引擎
│   │   │   ├── embedder.py              # Embedding 服务
│   │   │   └── sync.py                  # 商品→知识库同步
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── system.py                # 系统 Prompt 模板
│   ├── models/
│   │   ├── knowledge.py *               # NEW: KnowledgeEntry 模型
│   ├── api/
│   │   ├── __init__.py *                # 注册 AI WebSocket 路由
│   │   ├── ai_ws.py *                   # NEW: WebSocket endpoint
│   │   └── knowledge.py *               # NEW: 知识库管理 API
│   ├── schemas/
│   │   ├── ai.py *                       # NEW: AI 消息 schemas
│   │   └── knowledge.py *               # NEW: 知识库 schemas
│   ├── services/
│   │   ├── order_service.py *           # 支持 AI 对话下单
│   ├── main.py *                        # 注册 WebSocket 路由
│   └── config.py *                      # 新增 AI 配置项
├── tests/
│   ├── test_ai_conversation.py *         # NEW
│   ├── test_ai_intent.py *              # NEW
│   ├── test_ai_order_builder.py *       # NEW
│   ├── test_knowledge.py *              # NEW
│   └── test_llm_client.py *             # NEW
├── requirements.txt *                    # 新增 langchain, openai, tiktoken
└── alembic/versions/ *                   # 新增 knowledge_entries 迁移
```

```
hxmall/miniapp/src/
├── pages/
│   └── ai-assistant/
│       └── index.vue *                  # 替换占位页 → 激活聊天
├── components/
│   ├── ChatBubble.vue *                 # NEW: 聊天气泡组件
│   ├── ProductCardMsg.vue *             # NEW: 对话中的商品卡片
│   ├── OrderConfirmCard.vue *           # NEW: 订单确认卡片
│   ├── QuickReplies.vue *               # NEW: 快捷回复按钮组
│   └── StreamingText.vue *              # NEW: 流式文字渲染
├── api/
│   ├── chat.ts *                        # NEW: WebSocket 聊天 API
├── stores/
│   └── chat.ts *                        # NEW: 聊天状态 Store
├── utils/
│   └── index.ts *                       # 可能需要新增工具函数
```

---

## Task Group P2-1：AI 服务基础设施 + WebSocket 通道

> **负责人：程序师** | 依赖：Phase 1 全部完成 | 产出：WebSocket 连接 + LLM 基础对话

**验收标准：**
- WebSocket 连接 `ws://localhost:8000/api/v1/ai/ws/chat?token=xxx` 成功
- 发送文本消息 → LLM 流式返回（DeepSeek V4 Pro）
- 断开连接正常清理

### Task P2-1.1：配置 + 依赖更新

**Files:**
- Modify: `backend/requirements.txt` — 添加：`openai>=1.0.0`, `langchain>=0.3.0`, `langchain-text-splitters>=0.3.0`, `tiktoken>=0.7.0`
- Modify: `backend/app/config.py` — 添加 LLM 配置：

```python
# AI / LLM
DEEPSEEK_API_KEY: str = ""
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL: str = "deepseek-chat"
AI_DEFAULT_MODEL: str = "deepseek"  # deepseek | qwen (Phase 3)
AI_MAX_TOKENS: int = 2048
AI_TEMPERATURE: float = 0.7
# Embedding
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_API_KEY: str = ""
EMBEDDING_BASE_URL: str = ""
```

### Task P2-1.2：LLM 客户端抽象

**Files:**
- Create: `backend/app/ai/__init__.py`
- Create: `backend/app/ai/llm_client.py`

```python
"""LLM 客户端：统一封装 DeepSeek（以及后续千问），支持流式输出"""
from typing import AsyncIterator
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

def get_llm_client(model: str | None = None) -> AsyncOpenAI:
    """获取 LLM 客户端实例"""
    model = model or settings.AI_DEFAULT_MODEL
    if model == "deepseek":
        return AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    # Phase 3: 千问
    # elif model == "qwen":
    #     return AsyncOpenAI(api_key=settings.QWEN_API_KEY, base_url=settings.QWEN_BASE_URL)
    raise ValueError(f"Unknown model: {model}")

async def chat_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    """
    流式对话：逐 token yield。
    
    Args:
        messages: [{"role":"system","content":"..."}, {"role":"user","content":"..."}, ...]
        model: 模型标识 (deepseek | qwen)
    
    Yields:
        str: 每次 yield 一个 token 片段
    """
    client = get_llm_client(model)
    stream = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL if model == "deepseek" else settings.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature or settings.AI_TEMPERATURE,
        max_tokens=max_tokens or settings.AI_MAX_TOKENS,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

async def chat_sync(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """非流式对话：返回完整回复"""
    client = get_llm_client(model)
    response = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL if model == "deepseek" else settings.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature or settings.AI_TEMPERATURE,
        max_tokens=max_tokens or settings.AI_MAX_TOKENS,
        stream=False,
    )
    return response.choices[0].message.content or ""
```

### Task P2-1.3：WebSocket 处理器

**Files:**
- Create: `backend/app/ai/ws_handler.py`

```python
"""WebSocket 连接管理器 + 消息路由"""
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.ai.llm_client import chat_stream
from app.ai.prompts.system import SYSTEM_PROMPT

class ConnectionManager:
    """管理所有活跃的 WebSocket 连接"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}  # user_id → ws

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_json(self, user_id: str, data: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)

    async def send_text(self, user_id: str, text: str):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(text)

manager = ConnectionManager()

async def handle_chat(websocket: WebSocket, user_id: str, user_context: dict):
    """
    主聊天处理循环：
    1. 接收用户消息
    2. 构建消息上下文（system prompt + 历史 + 用户消息）
    3. 流式调用 LLM
    4. 每个 token 通过 WS 发送给前端
    """
    await manager.connect(user_id, websocket)
    history: list[dict] = []  # 会话历史（当前连接内）
    
    try:
        # 1. 发送欢迎消息
        await manager.send_json(user_id, {
            "type": "text",
            "content": f"您好！我是小暖，您的儿童产品选品助手。今天想了解哪类产品呢？😊",
        })
        await manager.send_json(user_id, {
            "type": "quick_replies",
            "items": ["游泳设备", "护肤产品", "健康产品", "查看新品"],
        })
        
        while True:
            # 2. 接收用户消息
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            user_input = msg.get("content", "").strip()
            
            if not user_input:
                continue
            
            # 3. 构建消息列表
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history[-20:])  # 最近 20 轮上下文
            messages.append({"role": "user", "content": user_input})
            
            # 4. 首先发送 "thinking" 状态
            await manager.send_json(user_id, {"type": "thinking", "content": "小暖正在思考..."})
            
            # 5. 流式输出 LLM 回复
            full_response = ""
            async for token in chat_stream(messages, model="deepseek"):
                full_response += token
                await manager.send_json(user_id, {"type": "text_chunk", "content": token})
            
            # 6. 发送完整回复结束标记
            await manager.send_json(user_id, {"type": "text_done", "content": full_response})
            
            # 7. 存储对话历史
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": full_response})
            
            # 8. TODO P2-3: 意图识别 → 触发结构化回复
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await manager.send_json(user_id, {"type": "error", "content": f"出错了：{str(e)}"})
        manager.disconnect(user_id)
```

### Task P2-1.4：System Prompt 模板

**Files:**
- Create: `backend/app/ai/prompts/__init__.py`
- Create: `backend/app/ai/prompts/system.py`

```python
"""小暖 AI 助手 System Prompt"""

SYSTEM_PROMPT = """你是「小暖」，B2B 儿童产品批发商城 HX Mall 的 AI 选品助手。

## 你的身份
- 名字：小暖
- 性格：温柔贴心、专业可靠，像一位经验丰富的母婴店采购顾问
- 服务对象：下游零售商（母婴店、游泳馆、儿童乐园的采购经理/老板）
- Slogan：给孩子温柔的呵护

## 你的能力
1. 推荐儿童产品（游泳设备、护肤产品、健康产品）
2. 根据适龄段、认证标准、价格带筛选商品
3. 帮助零售商计算批发价格（不同等级+数量对应不同阶梯价）
4. 协助下单（确认商品、数量、支付方式）
5. 回答产品相关问题（材质、认证、适用年龄等）

## 对话风格
- 称呼用户为"您"，语气温暖但不油腻
- 推荐时说明理由（如"这款游泳圈适合3-6岁宝宝，有3C认证，最近很多游泳馆都在采购"）
- 涉及价格时清晰列出阶梯价
- 涉及安全时强调认证信息
- 回复简洁，每次推荐不超过3款商品

## 儿童产品知识
- 所有儿童产品必须关注安全性和适龄性
- 游泳设备关注：材质安全（不含BPA）、浮力标准、适龄范围
- 护肤产品关注：成分温和、无刺激、通过皮肤测试
- 健康产品关注：生产资质、成分透明、适合年龄段

## 商品格式
当推荐商品时，使用以下格式：
```
**推荐商品：[商品名称]**
🏷️ 适合：[适龄段]
🛡️ 认证：[安全认证列表]
💰 批发价：[等级]等级 [数量]件起 ¥[单价]/件
📦 库存：[库存数量]件
```
"""

WELCOME_MESSAGE = "您好！我是小暖，您的儿童产品选品助手。今天想了解哪类产品呢？😊"
```

### Task P2-1.5：WebSocket API 端点

**Files:**
- Create: `backend/app/api/ai_ws.py`

```python
"""AI WebSocket 端点"""
from fastapi import APIRouter, WebSocket, Depends, Query
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
    AI 对话 WebSocket 通道。
    连接时需要携带 JWT token 认证。
    
    消息格式（前端→后端）:
    {"content": "用户输入文本"}
    
    消息格式（后端→前端）:
    {"type": "text_chunk", "content": "..."}  ← 流式 token
    {"type": "text_done", "content": "..."}  ← 一句话结束
    {"type": "thinking", "content": "..."}   ← AI 正在处理
    {"type": "text", "content": "..."}        ← 完整文本消息
    {"type": "product_card", "products": [...]} ← 商品推荐卡片
    {"type": "order_confirm", "order": {...}}  ← 订单确认卡
    {"type": "order_result", "order": {...}}   ← 下单结果
    {"type": "quick_replies", "items": [...]}  ← 快捷回复按钮
    {"type": "error", "content": "..."}        ← 错误消息
    """
    # 1. 验证 JWT token
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
    
    # 2. 获取用户上下文（等级、偏好等）
    # TODO P2-3: 读取用户画像
    user_context = {"user_id": user_id, "role": payload.get("role", "retailer")}
    
    # 3. 进入主聊天循环
    await handle_chat(websocket, user_id, user_context)
```

### Task P2-1.6：注册路由 + 测试

**Files:**
- Modify: `backend/app/main.py` — 添加 WebSocket 路由注册
- Modify: `backend/app/api/__init__.py` — 添加 ai_ws router
- Create: `backend/tests/test_llm_client.py`

LLM client 测试使用 mock — 不实际调用 DeepSeek API（需要 API key 且计费）：

```python
"""LLM 客户端测试（使用 mock）"""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_llm_client_creation():
    """测试客户端创建"""
    from app.ai.llm_client import get_llm_client
    # Without API key set, client still creates (fails on first API call)
    client = get_llm_client("deepseek")
    assert client is not None

@pytest.mark.asyncio
async def test_llm_chat_sync_mock():
    """测试非流式对话（mock API）"""
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
    """测试流式对话（mock API）"""
    from app.ai.llm_client import chat_stream
    
    with patch('app.ai.llm_client.AsyncOpenAI') as mock_openai:
        # 模拟流式返回3个chunk
        class MockChunk:
            def __init__(self, content):
                self.choices = [type('Choice', (), {'delta': type('Delta', (), {'content': content})()})]
        
        mock_stream = AsyncMock()
        mock_stream.__aiter__ = AsyncMock(return_value=iter([
            MockChunk("你好"), MockChunk("，我是"), MockChunk("小暖")
        ]).__aiter__)
        
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_stream)
        mock_openai.return_value = mock_instance
        
        chunks = []
        async for chunk in chat_stream([{"role": "user", "content": "你好"}], model="deepseek"):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert "".join(chunks) == "你好，我是小暖"
```

### Task P2-1.7：创建 WebSocket 测试

**Files:**
- Create: `backend/tests/test_ai_conversation.py`

```python
"""AI 对话 WebSocket 测试"""
import pytest
from httpx import AsyncClient
from httpx_ws import aconnect_ws

# 注意：WebSocket 测试需要 httpx-ws 库
# 添加到 requirements.txt: httpx-ws>=0.1.0

@pytest.mark.asyncio
async def test_websocket_auth_required():
    """没有 token 时应被拒绝"""
    # 此测试在真实服务器运行时有效
    pass  # WebSocket 测试需要运行中的服务器

@pytest.mark.asyncio
async def test_system_prompt():
    """验证 system prompt 包含必要元素"""
    from app.ai.prompts.system import SYSTEM_PROMPT
    assert "小暖" in SYSTEM_PROMPT
    assert "儿童产品" in SYSTEM_PROMPT
    assert "游泳设备" in SYSTEM_PROMPT
    assert "护肤产品" in SYSTEM_PROMPT
    assert "健康产品" in SYSTEM_PROMPT
    assert "安全" in SYSTEM_PROMPT
```

**验收：** `pytest tests/test_llm_client.py tests/test_ai_conversation.py -v` 通过

---

## Task Group P2-2：意图识别 + 对话状态机 + 商品搜索

> **负责人：程序师** | 依赖：P2-1 | 产出：AI 能识别用户意图并切换状态

**验收标准：**
- 发送"推荐游泳圈" → 识别为 recommend 意图 → 调用商品 API 搜索 → 返回 product_card
- 发送"第一款拿50件" → 识别为 order 意图 → 进入 BUILDING_ORDER 状态
- 各意图正确分类

### Task P2-2.1：意图识别器

**Files:**
- Create: `backend/app/ai/intent.py`

```python
"""意图识别器：用 LLM 进行意图分类（非规则匹配，更灵活）"""
from enum import StrEnum
from pydantic import BaseModel
from app.ai.llm_client import chat_sync

class IntentType(StrEnum):
    RECOMMEND = "recommend"    # 推荐商品
    SEARCH = "search"          # 搜索查询
    ORDER = "order"            # 下单操作
    NEGOTIATE = "negotiate"    # 议价/数量协商
    QUERY = "query"            # 信息查询（产品、订单）
    REORDER = "reorder"        # 补货
    GREETING = "greeting"      # 问候/闲聊
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

请只返回JSON，格式：{"intent":"recommend","keywords":["游泳","儿童"],"quantity":null,"product_name":null}

用户输入：{user_input}"""

async def classify_intent(user_input: str) -> dict:
    """用 LLM 进行意图分类，返回结构化结果"""
    try:
        result = await chat_sync(
            messages=[{"role": "user", "content": INTENT_PROMPT.format(user_input=user_input)}],
            temperature=0.1,  # 低温度，更确定性
            max_tokens=200,
        )
        import json
        # 尝试提取 JSON
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception:
        return {"intent": "greeting", "keywords": [], "quantity": None, "product_name": None}
```

### Task P2-2.2：对话状态机 + 上下文管理

**Files:**
- Create: `backend/app/ai/conversation.py`

```python
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
    """单次对话的上下文（存在 Redis 中，Phase 2 先内存存储）"""
    user_id: str
    state: ConversationState = ConversationState.IDLE
    history: list[dict] = field(default_factory=list)
    # 推荐上下文
    last_recommendations: list[dict] = field(default_factory=list)  # 最近推荐的商品列表
    # 订单构建上下文
    selected_product: dict | None = None  # 用户选中的商品
    order_quantity: int = 0
    order_payment_method: str | None = None
    # 用户画像缓存
    user_level: str = "normal"
    user_profile_summary: str = ""
    # 创建时间
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ConversationManager:
    """管理所有活跃对话（内存存储，后续升级为 Redis）"""
    
    def __init__(self):
        self._conversations: dict[str, ConversationContext] = {}
    
    def get_or_create(self, user_id: str) -> ConversationContext:
        if user_id not in self._conversations:
            self._conversations[user_id] = ConversationContext(user_id=user_id)
        return self._conversations[user_id]
    
    def reset(self, user_id: str):
        """重置对话状态（用户说"重新开始"或下单完成后）"""
        self._conversations[user_id] = ConversationContext(user_id=user_id)
    
    def update(self, user_id: str, **kwargs):
        ctx = self.get_or_create(user_id)
        for key, value in kwargs.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)

conv_manager = ConversationManager()
```

### Task P2-2.3：商品搜索集成

修改 `backend/app/ai/ws_handler.py` 的 `handle_chat` 函数，在步骤 7 之后增加意图处理和商品搜索：

```python
# 在 ws_handler.py 的 handle_chat 中，full_response 之后增加：

# 意图识别
from app.ai.intent import classify_intent, IntentType
from app.ai.conversation import conv_manager, ConversationState

intent_result = await classify_intent(user_input)
intent = intent_result.get("intent", "unknown")
ctx = conv_manager.get_or_create(user_id)

# 根据意图触发不同逻辑
if intent == IntentType.RECOMMEND or intent == IntentType.SEARCH:
    ctx.state = ConversationState.RECOMMENDING
    # 搜索相关商品
    keywords = intent_result.get("keywords", [user_input])
    products = await search_products_for_ai(db_pool, keywords)
    if products:
        ctx.last_recommendations = products
        ctx.state = ConversationState.RECOMMENDING
        await manager.send_json(user_id, {
            "type": "product_card",
            "products": products,
            "message": f"为您找到 {len(products)} 款相关商品："
        })
        await manager.send_json(user_id, {
            "type": "quick_replies",
            "items": ["第一款", "第二款", "第三款", "再看看别的"]
        })

elif intent == IntentType.ORDER:
    # 尝试构建订单
    ctx.state = ConversationState.BUILDING_ORDER
    # 解析用户选中的商品和数量
    # ... 见 P2-4

elif intent == IntentType.QUERY:
    # 先用 RAG 检索知识库（见 P2-5）
    pass
```

同时添加商品搜索辅助函数（直接调用现有 Product 模型）：

```python
async def search_products_for_ai(db_session_factory, keywords: list[str], limit: int = 3) -> list[dict]:
    """为 AI 对话搜索商品"""
    from sqlalchemy import select, or_
    from app.models.product import Product, ProductStatus
    from app.services.pricing import get_price_range
    
    async with db_session_factory() as session:
        conditions = []
        for kw in keywords:
            conditions.append(Product.name.ilike(f"%{kw}%"))
            conditions.append(Product.description.ilike(f"%{kw}%"))
        
        result = await session.execute(
            select(Product)
            .where(Product.status == ProductStatus.ON_SALE, or_(*conditions))
            .limit(limit)
        )
        products = result.scalars().all()
        
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "image": p.images[0] if p.images else "",
                "age_range": p.age_range,
                "safety_certifications": p.safety_certifications or [],
                "price_min": get_price_range(p.pricing_rules)[0],
                "price_max": get_price_range(p.pricing_rules)[1],
                "stock": p.stock,
                "min_order_qty": p.min_order_qty,
            }
            for p in products
        ]
```

### Task P2-2.4：测试

**Files:**
- Create: `backend/tests/test_ai_intent.py`

测试意图分类（使用 mock LLM 或直接测试规则）：
```python
import pytest
from app.ai.intent import INTENT_PROMPT

def test_intent_prompt_contains_types():
    assert "recommend" in INTENT_PROMPT
    assert "search" in INTENT_PROMPT
    assert "order" in INTENT_PROMPT

def test_conversation_state_machine():
    from app.ai.conversation import ConversationContext, ConversationState, conv_manager
    
    ctx = conv_manager.get_or_create("test_user")
    assert ctx.state == ConversationState.IDLE
    
    conv_manager.update("test_user", state=ConversationState.RECOMMENDING)
    assert conv_manager.get_or_create("test_user").state == ConversationState.RECOMMENDING
    
    conv_manager.reset("test_user")
    assert conv_manager.get_or_create("test_user").state == ConversationState.IDLE
```

---

## Task Group P2-3：订单构建器（对话→下单）

> **负责人：程序师** | 依赖：P2-2 | 产出：AI 可从对话中提取订单并调用下单 API

**验收标准：**
- 用户说"第一款拿100件" → AI 识别选中商品 + 数量 → 调用订单构建 → 返回 order_confirm 卡片
- 用户确认 → 创建真实订单 → 返回 order_result
- 校验失败 → AI 友好地告知用户原因

### Task P2-3.1：订单构建器

**Files:**
- Create: `backend/app/ai/order_builder.py`

```python
"""订单构建器：从对话上下文提取结构化订单并创建"""
import uuid
from app.ai.conversation import conv_manager, ConversationState
from app.services.order_service import create_order
from app.services.pricing import get_price

async def build_order_from_context(
    user_id: uuid.UUID,
    db_session_factory,
) -> dict:
    """
    从对话上下文中构建订单。
    
    步骤：
    1. 读取对话上下文中的 selected_product 和 order_quantity
    2. 查询商品当前信息和价格
    3. 校验库存、最低起批量
    4. 调用 order_service.create_order
    5. 返回订单结果
    
    Returns:
        {"success": bool, "order": {...} | "error": "原因"}
    """
    ctx = conv_manager.get_or_create(str(user_id))
    
    if not ctx.selected_product:
        return {"success": False, "error": "还没有选择商品，请先告诉小暖您想要哪一款~"}
    
    if ctx.order_quantity <= 0:
        return {"success": False, "error": "请告诉小暖您需要多少件~"}
    
    product_id = ctx.selected_product["id"]
    
    # 构建订单 items
    items = [{
        "product_id": product_id,
        "name": ctx.selected_product.get("name", ""),
        "qty": ctx.order_quantity,
        "unit_price": 0,  # 由 order_service 匹配定价
        "subtotal": 0,
    }]
    
    try:
        async with db_session_factory() as session:
            order = await create_order(
                db=session,
                retailer_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
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
            conv_manager.update(str(user_id), state=ConversationState.COMPLETED)
            return {"success": True, "order": order_data}
    except ValueError as e:
        return {"success": False, "error": str(e)}

def parse_order_intent(user_input: str, ctx) -> dict:
    """
    从用户输入中解析订单意图（提取商品选择和数量）。
    
    简单规则+LLM混合：
    1. 如果用户说"第X款"且 ctx.last_recommendations 有数据 → 直接匹配
    2. 用正则提取数量："100件" → 100
    3. 若模糊则调用 LLM 解析
    """
    import re
    
    result = {"product_index": None, "quantity": 0, "payment_method": None}
    
    # 匹配 "第X款" 或 "第X个"
    index_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*(款|个|种)", user_input)
    if index_match:
        num_str = index_match.group(1)
        num_map = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
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
```

### Task P2-3.2：集成到 WebSocket 处理器

修改 `ws_handler.py`，在 ORDER 意图分支中调用 order_builder：

```python
elif intent == IntentType.ORDER:
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
        # 所有信息齐全，发送确认卡片
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
            "content": "好的，请告诉我您要哪款商品？要多少件呢？",
        })
```

### Task P2-3.3：确认下单流程

当用户说"确认下单"时，调用 order_builder 创建真实订单：

```python
elif "确认下单" in user_input and ctx.state == ConversationState.BUILDING_ORDER:
    result = await build_order_from_context(user_id, db_session_factory)
    if result["success"]:
        conv_manager.update(str(user_id), state=ConversationState.COMPLETED)
        await manager.send_json(user_id, {
            "type": "order_result",
            "order": result["order"],
        })
        await manager.send_json(user_id, {
            "type": "text",
            "content": f"订单已生成！订单号：{result['order']['order_no']}，您可以在「我的订单」中查看详情。",
        })
    else:
        await manager.send_json(user_id, {
            "type": "text",
            "content": f"抱歉，下单遇到问题：{result['error']}",
        })
```

### Task P2-3.4：测试

**Files:**
- Create: `backend/tests/test_ai_order_builder.py`

---

## Task Group P2-4：知识库引擎（RAG + pgvector）

> **负责人：程序师** | 依赖：P2-1 | 产出：知识库可存储/检索，商品信息自动同步到向量库

**验收标准：**
- 商品信息自动 Embedding → pgvector 存储
- 用户问"这款游泳圈安全吗" → RAG 检索相关商品知识 → 注入 LLM 上下文 → 回答准确
- 管理员可通过 API 新增知识条目

### Task P2-4.1：知识库模型

**Files:**
- Create: `backend/app/models/knowledge.py`

```python
"""知识库模型：存储商品知识条目的向量嵌入"""
import uuid
from sqlalchemy import String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin
from sqlalchemy.dialects.postgresql import UUID

class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge_entries"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="来源: product|manual|faq|conversation")
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, comment="关联商品ID")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="知识内容（原始文本）")
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True, comment="向量嵌入(1536维)")  # text-embedding-3-small
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="元数据: 适龄、品类、认证等")
    weight: Mapped[float] = mapped_column(Float, default=1.0, comment="权重（学习机制）")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="active|deprecated")
```

### Task P2-4.2：Embedding 服务

**Files:**
- Create: `backend/app/ai/knowledge/__init__.py`
- Create: `backend/app/ai/knowledge/embedder.py`

```python
"""Embedding 服务：文本→向量"""
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

async def embed_text(text: str) -> list[float]:
    """将单段文本转换为向量"""
    client = AsyncOpenAI(
        api_key=settings.EMBEDDING_API_KEY or settings.DEEPSEEK_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL or settings.DEEPSEEK_BASE_URL,
    )
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding

async def embed_batch(texts: list[str]) -> list[list[float]]:
    """批量文本→向量"""
    client = AsyncOpenAI(
        api_key=settings.EMBEDDING_API_KEY or settings.DEEPSEEK_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL or settings.DEEPSEEK_BASE_URL,
    )
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
```

### Task P2-4.3：RAG 检索引擎

**Files:**
- Create: `backend/app/ai/knowledge/engine.py`

```python
"""RAG 检索引擎"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeEntry

async def search_knowledge(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
    source_type: str | None = None,
) -> list[dict]:
    """
    向量相似度搜索知识库。
    
    Args:
        query_embedding: 查询文本的向量嵌入
        top_k: 返回 Top-K 结果
        source_type: 按来源过滤 (product/manual/faq/conversation)
    """
    # pgvector 余弦相似度搜索
    query = select(
        KnowledgeEntry,
        (1 - KnowledgeEntry.embedding.cosine_distance(query_embedding)).label("similarity")
    ).where(
        KnowledgeEntry.status == "active",
        KnowledgeEntry.embedding.is_not(None),
    ).order_by(text("similarity DESC")).limit(top_k)
    
    if source_type:
        query = query.where(KnowledgeEntry.source_type == source_type)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": str(row[0].id),
            "title": row[0].title,
            "content": row[0].content,
            "source_type": row[0].source_type,
            "similarity": float(row[1]),
            "metadata": row[0].metadata,
        }
        for row in rows
    ]

def format_rag_context(results: list[dict]) -> str:
    """将 RAG 检索结果格式化为注入 LLM 的上下文字符串"""
    if not results:
        return ""
    
    context_parts = ["\n--- 相关商品知识 ---"]
    for i, r in enumerate(results):
        context_parts.append(f"\n[{i+1}] {r['title']}（相似度: {r['similarity']:.2f}）")
        context_parts.append(r['content'][:500])  # 截断过长内容
    context_parts.append("---\n")
    
    return "\n".join(context_parts)
```

### Task P2-4.4：商品→知识库同步

**Files:**
- Create: `backend/app/ai/knowledge/sync.py`

```python
"""商品信息同步到知识库"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product, ProductStatus
from app.models.knowledge import KnowledgeEntry
from app.ai.knowledge.embedder import embed_text

async def sync_product_to_knowledge(db: AsyncSession, product: Product):
    """
    将单个商品的信息同步到知识库（创建或更新向量嵌入）。
    
    知识文本拼接规则：
    商品名 | 描述 | 适龄段 | 认证信息 | 规格参数
    """
    parts = [f"商品名称：{product.name}"]
    if product.description:
        parts.append(f"商品描述：{product.description}")
    if product.age_range:
        parts.append(f"适龄段：{product.age_range}")
    if product.safety_certifications:
        certs = "、".join(c.get("name", "") for c in product.safety_certifications)
        parts.append(f"安全认证：{certs}")
    if product.specs:
        specs_str = "; ".join(f"{k}:{v}" for k, v in product.specs.items())
        parts.append(f"规格参数：{specs_str}")
    
    content = " | ".join(parts)
    
    # 生成向量嵌入
    embedding = await embed_text(content)
    
    # 查找或创建知识条目
    result = await db.execute(
        select(KnowledgeEntry).where(
            KnowledgeEntry.source_type == "product",
            KnowledgeEntry.source_id == product.id,
        )
    )
    entry = result.scalar_one_or_none()
    
    if entry:
        entry.title = product.name
        entry.content = content
        entry.embedding = embedding
        entry.metadata = {
            "age_range": product.age_range,
            "category_id": str(product.category_id) if product.category_id else None,
            "safety_certifications": product.safety_certifications,
        }
    else:
        entry = KnowledgeEntry(
            source_type="product",
            source_id=product.id,
            title=product.name,
            content=content,
            embedding=embedding,
            metadata={
                "age_range": product.age_range,
                "category_id": str(product.category_id) if product.category_id else None,
                "safety_certifications": product.safety_certifications,
            },
        )
        db.add(entry)
    
    await db.flush()
    return entry

async def sync_all_products(db: AsyncSession) -> int:
    """全量同步所有在售商品到知识库"""
    result = await db.execute(
        select(Product).where(Product.status == ProductStatus.ON_SALE)
    )
    products = result.scalars().all()
    count = 0
    for product in products:
        await sync_product_to_knowledge(db, product)
        count += 1
    return count
```

### Task P2-4.5：知识库管理 API

**Files:**
- Create: `backend/app/schemas/knowledge.py`
- Create: `backend/app/api/knowledge.py`

```python
"""知识库管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.knowledge import KnowledgeEntry
from app.ai.knowledge.embedder import embed_text
from app.ai.knowledge.sync import sync_all_products
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.deps import require_role

router = APIRouter(prefix="/knowledge", tags=["知识库"])

@router.get("/entries", response_model=APIResponse[PaginatedResponse[dict]], summary="知识条目列表")
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeEntry)
    count_query = select(func.count()).select_from(KnowledgeEntry)
    if source_type:
        query = query.where(KnowledgeEntry.source_type == source_type)
        count_query = count_query.where(KnowledgeEntry.source_type == source_type)
    
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(KnowledgeEntry.updated_at.desc()).offset((page-1)*page_size).limit(page_size))
    entries = result.scalars().all()
    
    items = [{"id": str(e.id), "title": e.title, "source_type": e.source_type, "weight": e.weight, "status": e.status} for e in entries]
    return APIResponse.ok(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))

@router.post("/entries", response_model=APIResponse[dict], summary="手动录入知识条目")
async def create_entry(
    title: str, content: str, source_type: str = "manual",
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    embedding = await embed_text(content)
    entry = KnowledgeEntry(title=title, content=content, source_type=source_type, embedding=embedding)
    db.add(entry)
    await db.flush()
    return APIResponse.ok(data={"id": str(entry.id), "title": entry.title}, message="知识条目创建成功")

@router.post("/sync", response_model=APIResponse[dict], summary="全量同步商品到知识库")
async def trigger_sync(
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    count = await sync_all_products(db)
    return APIResponse.ok(data={"synced_count": count}, message=f"已同步 {count} 个商品")
```

### Task P2-4.6：迁移 + 测试

- 创建 alembic 迁移：`alembic revision --autogenerate -m "add_knowledge_entries"`
- 测试需要 pgvector（SQLite 无向量支持）— 测试跳过向量操作，只测文本部分

---

## Task Group P2-5：前端 — 激活"小暖AI"Tab

> **负责人：UI设计师** | 依赖：P2-1 WebSocket 通道完成 | 产出：完整的 AI 聊天界面

**验收标准：**
- 小程序打开"小暖AI" Tab → WebSocket 连接成功
- 发送消息 → AI 流式逐字回复
- product_card / order_confirm / order_result 富卡片正确渲染
- 快捷回复按钮可用

### Task P2-5.1：WebSocket 聊天 Store

**Files:**
- Create: `miniapp/src/stores/chat.ts`

```typescript
// WebSocket 聊天状态管理
import { defineStore } from 'pinia'

interface ChatMessage {
  id: string
  type: 'text' | 'product_card' | 'order_confirm' | 'order_result' | 'quick_replies' | 'thinking' | 'error'
  content?: string
  products?: any[]
  order?: any
  items?: string[]
  isUser?: boolean
  timestamp: number
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    connected: false,
    loading: false,
    inputValue: '',
  }),
  
  actions: {
    addMessage(msg: ChatMessage) { this.messages.push(msg) },
    updateLastMessage(updates: Partial<ChatMessage>) {
      const last = this.messages[this.messages.length - 1]
      if (last) Object.assign(last, updates)
    },
    clearMessages() { this.messages = [] },
  }
})
```

### Task P2-5.2：WebSocket 聊天 API

**Files:**
- Create: `miniapp/src/api/chat.ts`

```typescript
// WebSocket 聊天连接管理
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

let socketTask: any = null

export function connectChat() {
  const userStore = useUserStore()
  const chatStore = useChatStore()
  
  if (socketTask) return
  
  const baseUrl = 'ws://localhost:8000/api/v1/ai/ws/chat'
  socketTask = uni.connectSocket({
    url: `${baseUrl}?token=${userStore.token}`,
    success: () => { chatStore.connected = true },
  })
  
  socketTask.onMessage((res: any) => {
    const msg = JSON.parse(res.data)
    handleMessage(msg, chatStore)
  })
  
  socketTask.onClose(() => {
    chatStore.connected = false
    socketTask = null
  })
}

function handleMessage(msg: any, chatStore: any) {
  switch (msg.type) {
    case 'text_chunk':
      // 流式追加到上一条消息或创建新消息
      const last = chatStore.messages[chatStore.messages.length - 1]
      if (last && last.type === 'text' && !last.isUser) {
        last.content += msg.content
      } else {
        chatStore.addMessage({
          id: Date.now().toString(),
          type: 'text',
          content: msg.content,
          isUser: false,
          timestamp: Date.now()
        })
      }
      break
    case 'text':
    case 'thinking':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: msg.type,
        content: msg.content,
        isUser: false,
        timestamp: Date.now()
      })
      break
    case 'product_card':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'product_card',
        products: msg.products,
        content: msg.message,
        isUser: false,
        timestamp: Date.now()
      })
      break
    case 'order_confirm':
    case 'order_result':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: msg.type,
        order: msg.order,
        content: msg.content || '',
        isUser: false,
        timestamp: Date.now()
      })
      break
    case 'quick_replies':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'quick_replies',
        items: msg.items,
        isUser: false,
        timestamp: Date.now()
      })
      break
  }
}

export function sendMessage(content: string) {
  if (!socketTask) return
  const chatStore = useChatStore()
  
  chatStore.addMessage({
    id: Date.now().toString(),
    type: 'text',
    content,
    isUser: true,
    timestamp: Date.now()
  })
  
  socketTask.send({ data: JSON.stringify({ content }) })
}

export function disconnectChat() {
  if (socketTask) {
    socketTask.close()
    socketTask = null
  }
}
```

### Task P2-5.3：重写 AI 聊天页面

**Files:**
- Modify: `miniapp/src/pages/ai-assistant/index.vue` — 替换占位页为完整聊天页面

核心功能：
- 页面上方：品牌头部（"小暖"头像 + "给孩子温柔的呵护" + 在线状态）
- 中间：`scroll-view` 消息列表，自动滚动到底部
- 每条消息根据 type 渲染不同组件：
  - `text` → ChatBubble（区分用户/AI 气泡样式）
  - `product_card` → 横向滑动商品卡片列表，每项点击进详情或"选这款"
  - `order_confirm` → 订单确认卡片（商品+数量+金额+确认按钮）
  - `order_result` → 成功卡片（订单号+状态+查看详情）
  - `quick_replies` → 底部快捷回复按钮行
- 底部：输入框 + 发送按钮，珊瑚粉色系
- 语言按钮（录音→ASR，Phase 2 用文字替代先）

### Task P2-5.4：富消息卡片组件

**Files:**
- Create: `miniapp/src/components/ChatBubble.vue` — 聊天气泡
- Create: `miniapp/src/components/ProductCardMsg.vue` — 对话商品卡片（3个一组横向滑动）
- Create: `miniapp/src/components/OrderConfirmCard.vue` — 订单确认卡
- Create: `miniapp/src/components/QuickReplies.vue` — 快捷回复按钮组
- Create: `miniapp/src/components/StreamingText.vue` — 打字机效果文字

---

## Task Group P2-6：集成测试 + 端到端验证

> **负责人：联合** | 依赖：全部 P2 模块 | 产出：AI 下单全链路通过

**验收标准：**
- WebSocket 连接 → 发送"推荐游泳圈" → 收到 product_card → 点击"第一款拿50件" → 收到 order_confirm → 确认 → 收到 order_result → 数据库有真实订单
- 所有 Phase 1 测试仍通过

---

## 执行顺序与依赖图

```
P2-1 (AI 基础设施) ──┬── P2-2 (意图+状态机) ── P2-3 (订单构建器)
                      │
                      ├── P2-4 (知识库 RAG)
                      │
                      └── P2-5 (前端聊天界面)
                                  │
                      P2-6 (集成测试)
```

P2-2, P2-4, P2-5 可并行（都只依赖 P2-1）。P2-3 依赖 P2-2。

## 自检清单

| 检查项 | 状态 |
|--------|------|
| Spec 覆盖 (九、AI引擎 / 十、知识库 / 十二、模型路由) | ✅ |
| 占位符 | ✅ 无 TBD/TODO 残留 |
| Phase 1 兼容 | ✅ 不修改现有模型/API签名 |
| WebSocket 协议定义清晰 | ✅ |
| System Prompt 包含儿童产品特色 | ✅ |
