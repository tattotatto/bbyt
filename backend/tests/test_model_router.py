"""模型路由测试"""
def test_route_chat_to_deepseek():
    from app.ai.model_router import route_model
    assert route_model("chat") == "deepseek"


def test_route_recommend_to_qwen():
    from app.ai.model_router import route_model
    assert route_model("recommend") == "qwen"


def test_route_unknown_falls_back():
    from app.ai.model_router import route_model
    result = route_model("unknown_scenario")
    assert result in ("deepseek", "qwen")


def test_failover_from_deepseek():
    from app.ai.model_router import get_failover_model
    assert get_failover_model("deepseek") == "qwen"


def test_failover_last_model_returns_none():
    from app.ai.model_router import get_failover_model
    assert get_failover_model("qwen") is None


def test_llm_client_supports_qwen():
    from app.ai.llm_client import get_llm_client
    from unittest.mock import patch
    with patch("app.ai.llm_client.AsyncOpenAI") as mock_client:
        mock_client.return_value = "fake_client"
        client = get_llm_client("qwen")
        assert client is not None
        mock_client.assert_called_once()
