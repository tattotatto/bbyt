"""促销 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.promotion import Promotion
from app.schemas.common import APIResponse
from app.services.promotion import get_active_promotions, apply_promotion
from app.api.deps import require_role

router = APIRouter()


@router.get("/active", response_model=APIResponse[list[dict]], summary="当前促销")
async def active_promotions(db: AsyncSession = Depends(get_db)):
    promos = await get_active_promotions(db)
    return APIResponse.ok(data=[{
        "id": str(p.id), "title": p.title, "type": p.type.value,
        "rules": p.rules, "product_ids": p.product_ids,
        "start_time": p.start_time.isoformat() if p.start_time else None,
        "end_time": p.end_time.isoformat() if p.end_time else None,
    } for p in promos])


@router.post("/", response_model=APIResponse[dict], summary="创建促销（管理员）")
async def create_promotion(
    req: dict,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    promo = Promotion(
        title=req["title"], type=req["type"], rules=req["rules"],
        product_ids=req.get("product_ids"), start_time=req["start_time"],
        end_time=req["end_time"],
    )
    db.add(promo)
    await db.flush()
    return APIResponse.ok(data={"id": str(promo.id)}, message="促销创建成功")
