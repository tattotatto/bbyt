"""Embedding 服务：文本→向量"""
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()


async def embed_text(text: str) -> list[float]:
    """将单段文本转换为向量（使用配置的 Embedding 模型）"""
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
