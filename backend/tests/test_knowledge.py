"""知识库测试"""
import pytest


def test_knowledge_model_import():
    """验证知识库模型可导入"""
    from app.models.knowledge import KnowledgeEntry

    assert KnowledgeEntry.__tablename__ == "knowledge_entries"


def test_build_product_knowledge_text():
    """测试商品知识文本拼接"""
    import asyncio
    from app.ai.knowledge.sync import build_product_knowledge_text

    class MockProduct:
        name = "儿童游泳圈"
        description = "安全材质游泳圈"
        age_range = "3-6岁"
        safety_certifications = [{"name": "3C认证", "icon": "url"}]
        specs = {"材质": "PVC", "颜色": "黄色"}

    text = asyncio.run(build_product_knowledge_text(MockProduct()))
    assert "儿童游泳圈" in text
    assert "安全材质游泳圈" in text
    assert "3-6岁" in text
    assert "3C认证" in text


def test_cosine_similarity():
    """测试余弦相似度计算"""
    from app.ai.knowledge.engine import cosine_similarity

    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(1.0, 0.001)

    c = [0.0, 1.0, 0.0]
    assert cosine_similarity(a, c) == pytest.approx(0.0, 0.001)


def test_cosine_similarity_empty():
    """测试空向量余弦相似度"""
    from app.ai.knowledge.engine import cosine_similarity

    assert cosine_similarity([], [1.0, 0.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], []) == 0.0
    assert cosine_similarity(None, [1.0, 0.0]) == 0.0


def test_format_rag_context():
    """测试 RAG 上下文格式化"""
    from app.ai.knowledge.engine import format_rag_context

    results = [
        {"title": "游泳圈认证", "content": "3C认证是基本要求"},
        {"title": "材质要求", "content": "食品级PVC材质"},
    ]
    ctx = format_rag_context(results)
    assert "游泳圈认证" in ctx
    assert "3C认证是基本要求" in ctx
    assert "材质要求" in ctx


def test_format_rag_context_empty():
    """测试空结果的 RAG 上下文格式化"""
    from app.ai.knowledge.engine import format_rag_context

    assert format_rag_context([]) == ""


@pytest.mark.asyncio
async def test_sync_product_to_knowledge(client):
    """测试商品同步到知识库（端到端）"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    # 创建 admin
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.phone == "13800138030")
        )
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                phone="13800138030",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.add(admin)
            await session.commit()

    resp = await client.post(
        "/api/v1/auth/login", json={"phone": "13800138030", "password": "admin123"}
    )
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建品类
    resp = await client.post(
        "/api/v1/products/categories", json={"name": "测试"}, headers=headers
    )
    cat_id = resp.json()["data"]["id"]

    # 创建商品
    resp = await client.post(
        "/api/v1/products/",
        json={
            "category_id": cat_id,
            "name": "测试商品_知识库",
            "stock": 100,
            "min_order_qty": 10,
            "age_range": "3-6岁",
            "safety_certifications": [{"name": "3C认证"}],
            "pricing_rules": {"normal": [{"qty": 10, "price": 10.0}]},
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    product_id = resp.json()["data"]["id"]

    # 将商品上架（sync_all_products 只同步在售商品）
    from uuid import UUID
    from app.models.product import Product, ProductStatus
    async with async_session_factory() as session:
        result = await session.execute(
            select(Product).where(Product.id == UUID(product_id))
        )
        product = result.scalar_one()
        product.status = ProductStatus.ON_SALE
        await session.commit()

    # 同步
    resp = await client.post("/api/v1/knowledge/sync", headers=headers)
    assert resp.status_code == 200

    # 验证知识条目已创建
    resp = await client.get(
        "/api/v1/knowledge/entries?source_type=product", headers=headers
    )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any("测试商品_知识库" in item["title"] for item in items)


@pytest.mark.asyncio
async def test_manual_create_entry(client):
    """测试手动录入知识条目"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.phone == "13800138031")
        )
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                phone="13800138031",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.add(admin)
            await session.commit()

    resp = await client.post(
        "/api/v1/auth/login", json={"phone": "13800138031", "password": "admin123"}
    )
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/knowledge/entries",
        json={
            "title": "儿童游泳设备安全标准",
            "content": "儿童游泳设备必须符合GB 6675-2014《玩具安全》标准，不含BPA、邻苯二甲酸酯等有害物质。",
            "source_type": "manual",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["title"] == "儿童游泳设备安全标准"


@pytest.mark.asyncio
async def test_knowledge_requires_admin(client):
    """测试非管理员不能操作知识库"""
    resp = await client.post(
        "/api/v1/knowledge/entries",
        json={
            "title": "test",
            "content": "test",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_entries_pagination(client):
    """测试知识条目列表分页"""
    from app.models.user import User, UserRole, UserStatus
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.phone == "13800138032")
        )
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                phone="13800138032",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.add(admin)
            await session.commit()

    resp = await client.post(
        "/api/v1/auth/login", json={"phone": "13800138032", "password": "admin123"}
    )
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建几条手动知识条目
    for i in range(3):
        resp = await client.post(
            "/api/v1/knowledge/entries",
            json={
                "title": f"测试条目{i}",
                "content": f"测试内容{i}",
                "source_type": "manual",
            },
            headers=headers,
        )
        assert resp.status_code == 200

    # 列表查询
    resp = await client.get("/api/v1/knowledge/entries", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
