"""用户管理接口测试"""
import pytest
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import create_access_token, hash_password


@pytest.mark.asyncio
async def test_user_list_includes_nickname_for_wx_user(client, db_session):
    """微信登录用户（phone=wx_ 前缀）在管理端列表中应带 nickname，供前端展示而非显示伪 openid"""
    admin = User(phone="13800000000", hashed_password=hash_password("admin123"),
                 role=UserRole.ADMIN, status=UserStatus.ACTIVE)
    db_session.add(admin)
    wx_user = User(phone="wx_" + "a" * 17, hashed_password=hash_password("x"),
                   role=UserRole.RETAILER, status=UserStatus.PENDING_REVIEW,
                   nickname="小暖用户")
    db_session.add(wx_user)
    await db_session.flush()

    token = create_access_token(admin.id, admin.role.value)
    res = await client.get("/api/v1/users?role=retailer",
                           headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    wx_item = next((i for i in items if i["phone"].startswith("wx_")), None)
    assert wx_item is not None
    assert wx_item["nickname"] == "小暖用户"
