"""地址簿 API 测试"""
import uuid, pytest
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import create_access_token, hash_password


async def _mk_retailer(db_session, phone: str):
    u = User(phone=phone, hashed_password=hash_password("pass1234"),
             role=UserRole.RETAILER, status=UserStatus.ACTIVE)
    db_session.add(u); await db_session.flush()
    return u, create_access_token(u.id, u.role.value)


def _addr(payload: dict) -> dict:
    base = {"name": "张三", "phone": "13800000000", "province": "广东省",
            "city": "深圳市", "district": "南山区", "detail": "科技园路1号"}
    base.update(payload)
    return base


@pytest.mark.asyncio
async def test_address_crud_and_default(client, db_session):
    u, token = await _mk_retailer(db_session, "13900000031")
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/api/v1/users/addresses", json=_addr({"is_default": True}), headers=h)
    assert r1.status_code == 200
    aid = r1.json()["data"]["id"]
    r2 = await client.post("/api/v1/users/addresses", json=_addr({"name": "李四"}), headers=h)
    assert r2.status_code == 200
    lst = (await client.get("/api/v1/users/addresses", headers=h)).json()["data"]
    assert len(lst) == 2
    assert lst[0]["id"] == aid and lst[0]["is_default"] is True  # 默认置顶
    # 把第二条设为默认 → 第一条默认被清
    aid2 = lst[1]["id"]
    await client.put(f"/api/v1/users/addresses/{aid2}", json={"is_default": True}, headers=h)
    lst2 = (await client.get("/api/v1/users/addresses", headers=h)).json()["data"]
    assert sum(1 for a in lst2 if a["is_default"]) == 1
    # 部分更新
    res = await client.put(f"/api/v1/users/addresses/{aid}", json={"detail": "新地址2号"}, headers=h)
    assert res.status_code == 200
    assert res.json()["data"]["detail"] == "新地址2号"
    # 删除
    await client.delete(f"/api/v1/users/addresses/{aid}", headers=h)
    lst3 = (await client.get("/api/v1/users/addresses", headers=h)).json()["data"]
    assert len(lst3) == 1


@pytest.mark.asyncio
async def test_address_other_user_403(client, db_session):
    u1, token1 = await _mk_retailer(db_session, "13900000032")
    u2, token2 = await _mk_retailer(db_session, "13900000033")
    await client.post("/api/v1/users/addresses", json=_addr({}), headers={"Authorization": f"Bearer {token1}"})
    aid = (await client.get("/api/v1/users/addresses",
                            headers={"Authorization": f"Bearer {token1}"})).json()["data"][0]["id"]
    res = await client.put(f"/api/v1/users/addresses/{aid}", json={"detail": "x"},
                           headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403
    res = await client.delete(f"/api/v1/users/addresses/{aid}",
                              headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_address_requires_auth(client, db_session):
    assert (await client.get("/api/v1/users/addresses")).status_code == 401
