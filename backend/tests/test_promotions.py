import pytest


@pytest.mark.asyncio
async def test_list_promotions_empty(client):
    resp = await client.get("/api/v1/promotions/active")
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)


def test_apply_full_reduction():
    from app.services.promotion import apply_promotion
    from app.models.promotion import Promotion, PromotionType
    promo = Promotion(type=PromotionType.FULL_REDUCTION, rules={"threshold": 100000, "reduce": 10000})
    result = apply_promotion(150000, promo)
    assert result == 140000  # 1500 - 100 = 1400元


def test_apply_discount():
    from app.services.promotion import apply_promotion
    from app.models.promotion import Promotion, PromotionType
    promo = Promotion(type=PromotionType.DISCOUNT, rules={"rate": 0.85})
    result = apply_promotion(100000, promo)
    assert result == 85000  # 1000 * 0.85
