"""商品信息同步到知识库"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product, ProductStatus
from app.models.knowledge import KnowledgeEntry
from app.ai.knowledge.embedder import embed_text


async def build_product_knowledge_text(product: Product) -> str:
    """拼接商品的知识文本"""
    parts = [f"商品名称：{product.name}"]
    if product.description:
        parts.append(f"商品描述：{product.description}")
    if product.age_range:
        parts.append(f"适龄段：{product.age_range}")
    if product.safety_certifications:
        certs = "、".join(
            c.get("name", "") for c in (product.safety_certifications or [])
        )
        parts.append(f"安全认证：{certs}")
    if product.specs:
        specs_str = "; ".join(f"{k}:{v}" for k, v in product.specs.items())
        parts.append(f"规格参数：{specs_str}")
    return " | ".join(parts)


async def sync_product_to_knowledge(
    db: AsyncSession, product: Product
) -> KnowledgeEntry | None:
    """同步单个商品到知识库（创建或更新）"""
    content = await build_product_knowledge_text(product)

    # 尝试生成向量嵌入（如果没有配置 API key 则跳过）
    embedding = None
    try:
        embedding = await embed_text(content)
    except Exception:
        pass  # 没有 Embedding API 时，仅用关键词搜索

    # 查找或创建
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
        if embedding:
            entry.embedding = embedding
        entry.meta_info = {
            "age_range": product.age_range,
            "category_id": str(product.category_id) if product.category_id else None,
            "certifications": product.safety_certifications,
        }
    else:
        entry = KnowledgeEntry(
            source_type="product",
            source_id=product.id,
            title=product.name,
            content=content,
            embedding=embedding,
            meta_info={
                "age_range": product.age_range,
                "category_id": str(product.category_id) if product.category_id else None,
                "certifications": product.safety_certifications,
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
