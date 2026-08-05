"""报表 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.common import APIResponse
from app.services.reports import generate_purchase_report

router = APIRouter()


@router.get("/purchase", response_model=APIResponse[dict], summary="采购分析报表")
async def purchase_report(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await generate_purchase_report(current_user["user_id"], db)
    return APIResponse.ok(data=report)
