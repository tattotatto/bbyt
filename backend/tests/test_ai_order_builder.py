"""订单构建器测试"""
import pytest


def test_parse_order_intent_chinese_index():
    """测试解析"第一款"等中文序号"""
    from app.ai.order_builder import parse_order_intent
    from app.ai.conversation import ConversationContext

    ctx = ConversationContext(user_id="test")
    result = parse_order_intent("第一款拿100件", ctx)
    assert result["product_index"] == 1
    assert result["quantity"] == 100


def test_parse_order_intent_digit_index():
    """测试解析数字序号"""
    from app.ai.order_builder import parse_order_intent
    from app.ai.conversation import ConversationContext

    ctx = ConversationContext(user_id="test")
    result = parse_order_intent("第3个，50件", ctx)
    assert result["product_index"] == 3
    assert result["quantity"] == 50


def test_parse_order_intent_payment_wechat():
    """测试解析微信支付"""
    from app.ai.order_builder import parse_order_intent
    from app.ai.conversation import ConversationContext

    ctx = ConversationContext(user_id="test")
    result = parse_order_intent("第一款100件，微信支付", ctx)
    assert result["payment_method"] == "wechat_pay"


def test_parse_order_intent_payment_bank():
    """测试解析银行转账"""
    from app.ai.order_builder import parse_order_intent
    from app.ai.conversation import ConversationContext

    ctx = ConversationContext(user_id="test")
    result = parse_order_intent("100件，走银行转账", ctx)
    assert result["payment_method"] == "bank_transfer"


def test_parse_order_intent_no_match():
    """测试无匹配时返回默认值"""
    from app.ai.order_builder import parse_order_intent
    from app.ai.conversation import ConversationContext

    ctx = ConversationContext(user_id="test")
    result = parse_order_intent("随便看看", ctx)
    assert result["product_index"] is None
    assert result["quantity"] == 0
    assert result["payment_method"] is None


@pytest.mark.asyncio
async def test_build_order_without_product():
    """测试没有选择商品时构建订单 - 应返回错误"""
    from app.ai.order_builder import build_order_from_context
    from app.ai.conversation import conv_manager

    conv_manager.reset("test_no_product")
    result = await build_order_from_context("test_no_product", None)
    assert result["success"] is False
    assert "商品" in result["error"]


@pytest.mark.asyncio
async def test_build_order_without_quantity():
    """测试选择了商品但没选数量"""
    from app.ai.order_builder import build_order_from_context
    from app.ai.conversation import conv_manager

    conv_manager.update("test_no_qty", selected_product={"id": "xxx", "name": "test"}, order_quantity=0)
    result = await build_order_from_context("test_no_qty", None)
    assert result["success"] is False
    assert "多少件" in result["error"]
