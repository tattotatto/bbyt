"""LLM 客户端：统一封装 DeepSeek（OpenAI 兼容 API），支持流式输出"""
from typing import AsyncIterator
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()


def get_llm_client(model: str | None = None) -> AsyncOpenAI:
    """获取 LLM 客户端实例。model: deepseek | qwen"""
    model = model or settings.AI_DEFAULT_MODEL
    if model == "deepseek":
        return AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    elif model == "qwen":
        return AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
        )
    raise ValueError(f"Unknown model: {model}")


async def chat_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    """流式对话：逐 token yield。用于 WebSocket 实时推送给前端。"""
    client = get_llm_client(model)
    stream = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
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
    """非流式对话：返回完整回复。用于意图识别等场景。"""
    client = get_llm_client(model)
    response = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature or settings.AI_TEMPERATURE,
        max_tokens=max_tokens or settings.AI_MAX_TOKENS,
        stream=False,
    )
    return response.choices[0].message.content or ""
