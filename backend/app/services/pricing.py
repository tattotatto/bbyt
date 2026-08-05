"""定价引擎：根据零售商等级和采购数量匹配阶梯价格"""
from decimal import Decimal


def get_price(level: str, qty: int, pricing_rules: dict) -> tuple[Decimal | None, Decimal | None]:
    """
    根据用户等级和数量匹配价格。

    Args:
        level: 零售商等级 (normal/silver/gold/platinum)
        qty: 采购数量
        pricing_rules: 定价矩阵 {"gold": [{"qty":10,"price":80},...], ...}

    Returns:
        (unit_price, total_price) 均为 Decimal，匹配不到时返回 (None, None)
    """
    rules = pricing_rules.get(level, pricing_rules.get("normal", []))
    if not rules:
        return None, None

    # Sort by qty ascending, find highest tier where qty >= tier_qty
    sorted_rules = sorted(rules, key=lambda r: r["qty"])
    matched = None
    for rule in sorted_rules:
        if qty >= rule["qty"]:
            matched = rule

    if matched is None:
        return None, None  # qty below minimum order

    unit_price = Decimal(str(matched["price"]))
    total_price = unit_price * qty
    return unit_price, total_price


def get_price_range(pricing_rules: dict) -> tuple[float | None, float | None]:
    """
    从定价矩阵中提取价格区间（用于商品列表展示）。
    Returns (min_price, max_price)
    """
    all_prices = []
    for level_rules in pricing_rules.values():
        for tier in level_rules:
            all_prices.append(tier["price"])
    if not all_prices:
        return None, None
    return float(min(all_prices)), float(max(all_prices))
