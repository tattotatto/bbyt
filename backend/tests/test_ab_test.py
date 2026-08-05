def test_assign_variant_consistent():
    from app.services.ab_test import assign_variant
    v1 = assign_variant("ai_model", "user_123")
    v2 = assign_variant("ai_model", "user_123")
    assert v1 == v2  # 同一用户始终同一变体


def test_assign_variant_distributes():
    from app.services.ab_test import assign_variant
    results = {"deepseek": 0, "qwen": 0}
    for i in range(100):
        results[assign_variant("ai_model", f"user_{i}")] += 1
    # 大致均匀分布
    assert results["deepseek"] > 30
    assert results["qwen"] > 30
