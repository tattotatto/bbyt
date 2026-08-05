"""文档解析器测试"""
import pytest
import tempfile
import os


@pytest.mark.asyncio
async def test_parse_txt():
    """测试 TXT 解析"""
    from app.ai.knowledge.parser import parse_document

    # 创建临时 txt 文件
    content = "这是测试内容。\n第二行内容。"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name

    result = await parse_document(tmp_path, "txt")
    assert "测试内容" in result

    os.unlink(tmp_path)


def test_parser_unsupported_type():
    """不支持的格式应抛异常"""
    import pytest
    from app.ai.knowledge.parser import parse_document

    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(parse_document("test.xyz", "xyz"))


def test_recommender_restock_imports():
    """验证推荐引擎可导入"""
    from app.services.recommender import get_homepage_recommendations, get_restock_suggestions
    assert callable(get_homepage_recommendations)
    assert callable(get_restock_suggestions)
