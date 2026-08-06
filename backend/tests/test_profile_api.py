"""企业资料更新 API 测试（Task A9）"""
import pytest
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import create_access_token, hash_password


async def _mk_user(db_session, phone: str, role=UserRole.RETAILER):
    u = User(phone=phone, hashed_password=hash_password("pass1234"),
             role=role, status=UserStatus.ACTIVE)
    db_session.add(u)
    await db_session.flush()
    return u, create_access_token(u.id, u.role.value)


@pytest.mark.asyncio
async def test_update_profile_partial(client, db_session):
    u, token = await _mk_user(db_session, "13900000061")
    h = {"Authorization": f"Bearer {token}"}
    # 无 profile 时更新应自动创建
    r1 = await client.put("/api/v1/users/me/profile", json={"company_name": "星辰贸易"}, headers=h)
    assert r1.status_code == 200
    assert r1.json()["data"]["retailer_profile"]["company_name"] == "星辰贸易"
    # 部分更新其余字段
    r2 = await client.put("/api/v1/users/me/profile",
                          json={"contact_person": "王五", "business_license": "BL2026"},
                          headers=h)
    assert r2.status_code == 200
    data = r2.json()["data"]["retailer_profile"]
    assert data["company_name"] == "星辰贸易"  # 已存在字段不受影响
    assert data["contact_person"] == "王五"


@pytest.mark.asyncio
async def test_update_profile_rejects_non_retailer(client, db_session):
    u, token = await _mk_user(db_session, "13900000062", role=UserRole.ADMIN)
    res = await client.put("/api/v1/users/me/profile",
                           json={"company_name": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_update_profile_requires_auth(client, db_session):
    res = await client.put("/api/v1/users/me/profile", json={"company_name": "x"})
    assert res.status_code == 401
