"""RAG 检索引擎：向量相似度 + 关键词混合搜索"""
import math
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeEntry


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def search_knowledge(
    db: AsyncSession,
    query_embedding: list[float] | None = None,
    query_text: str | None = None,
    top_k: int = 5,
    source_type: str | None = None,
) -> list[dict]:
    """
    搜索知识库（向量相似度 + 关键词混合）。

    Args:
        query_embedding: 查询向量（可选，用于语义搜索）
        query_text: 查询文本（可选，用于关键词搜索）
        top_k: 返回 Top-K 结果
        source_type: 按来源过滤
    """
    query = select(KnowledgeEntry).where(KnowledgeEntry.status == "active")

    if source_type:
        query = query.where(KnowledgeEntry.source_type == source_type)

    # 关键词搜索
    if query_text and not query_embedding:
        query = query.where(
            or_(
                KnowledgeEntry.title.ilike(f"%{query_text}%"),
                KnowledgeEntry.content.ilike(f"%{query_text}%"),
            )
        )

    result = await db.execute(query.limit(top_k * 3))  # 多取一些用于向量排序
    entries = result.scalars().all()

    # 如果有向量，按相似度排序
    if query_embedding and entries:
        scored = []
        for entry in entries:
            if entry.embedding:
                score = cosine_similarity(query_embedding, entry.embedding)
            else:
                score = 0.0
            scored.append((entry, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        entries = [s[0] for s in scored[:top_k]]
    else:
        entries = entries[:top_k]

    return [
        {
            "id": str(e.id),
            "title": e.title,
            "content": e.content,
            "source_type": e.source_type,
            "meta_info": e.meta_info,
        }
        for e in entries
    ]


def format_rag_context(results: list[dict]) -> str:
    """将 RAG 检索结果格式化为注入 LLM 的上下文"""
    if not results:
        return ""

    parts = ["\n--- 相关商品知识（供小暖参考） ---"]
    for i, r in enumerate(results):
        parts.append(f"\n[{i + 1}] {r['title']}")
        parts.append(r["content"][:500])
    parts.append("---\n")

    return "\n".join(parts)
