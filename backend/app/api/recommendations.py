"""推荐 API 端点"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.common import APIResponse
from app.services.recommender import get_homepage_recommendations, get_restock_suggestions

router = APIRouter()

@router.get("/homepage", response_model=APIResponse[list[dict]], summary="首页推荐")
async def homepage_recommend(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_homepage_recommendations(current_user["user_id"], db, limit)
    return APIResponse.ok(data=items)

@router.get("/restock", response_model=APIResponse[list[dict]], summary="补货建议")
async def restock_suggest(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_restock_suggestions(current_user["user_id"], db)
    return APIResponse.ok(data=items)
