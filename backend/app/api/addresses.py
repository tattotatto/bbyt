"""收货地址 API 端点"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate, AddressOut
from app.schemas.common import APIResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/addresses", response_model=APIResponse[list[AddressOut]], summary="我的地址列表")
async def list_addresses(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收货地址列表，默认地址置顶"""
    result = await db.execute(
        select(Address)
        .where(Address.user_id == current_user["user_id"])
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    addresses = result.scalars().all()
    return APIResponse.ok(data=addresses)


@router.post("/addresses", response_model=APIResponse[AddressOut], summary="新增收货地址")
async def create_address(
    req: AddressCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新增收货地址。若 is_default 为 True，先清该用户其余地址的默认标记"""
    if req.is_default:
        await db.execute(
            update(Address)
            .where(Address.user_id == current_user["user_id"])
            .values(is_default=False)
        )
    address = Address(
        user_id=current_user["user_id"],
        name=req.name,
        phone=req.phone,
        province=req.province,
        city=req.city,
        district=req.district,
        detail=req.detail,
        is_default=req.is_default,
    )
    db.add(address)
    await db.flush()
    await db.refresh(address)
    return APIResponse.ok(data=address, message="地址已保存")


@router.put("/addresses/{address_id}", response_model=APIResponse[AddressOut], summary="更新收货地址")
async def update_address(
    address_id: UUID,
    req: AddressUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """部分更新收货地址。仅本人可操作"""
    result = await db.execute(select(Address).where(Address.id == address_id))
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")

    if address.user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该地址")

    # exclude_unset 部分更新
    update_data = req.model_dump(exclude_unset=True)

    # 若更新后 is_default=True，先清其余地址的默认标记
    if update_data.get("is_default"):
        await db.execute(
            update(Address)
            .where(Address.user_id == current_user["user_id"])
            .values(is_default=False)
        )

    for key, value in update_data.items():
        setattr(address, key, value)

    await db.flush()
    await db.refresh(address)
    return APIResponse.ok(data=address, message="地址已更新")


@router.delete("/addresses/{address_id}", response_model=APIResponse, summary="删除收货地址")
async def delete_address(
    address_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除收货地址。仅本人可操作"""
    result = await db.execute(select(Address).where(Address.id == address_id))
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")

    if address.user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该地址")

    await db.delete(address)
    await db.flush()
    return APIResponse.ok(message="已删除")
