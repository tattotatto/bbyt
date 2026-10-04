"""案例图库测试"""
import pytest
from httpx import AsyncClient


async def login_admin(client: AsyncClient) -> str:
    from app.models.user import User, UserStatus, UserRole
    from app.database import async_session_factory
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    admin_phone = "13800138010"

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == admin_phone))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                phone=admin_phone, hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN, status=UserStatus.ACTIVE,
            )
            session.add(user)
            await session.commit()

    resp = await client.post("/api/v1/auth/login", json={"phone": admin_phone, "password": "admin123"})
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_create_case(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/cases/", json={
        "title": "婴童游泳馆 — 海洋主题",
        "description": "以海洋为灵感，打造梦幻儿童游泳空间",
        "images": ["https://example.com/case1-1.jpg", "https://example.com/case1-2.jpg"],
        "category_tags": ["婴童游泳馆"],
        "style_tags": ["卡通童趣"],
        "store_area_range": "100-200㎡",
        "is_featured": True,
        "sort_order": 10,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "婴童游泳馆 — 海洋主题"
    assert len(data["images"]) == 2
    assert data["is_featured"] == True


@pytest.mark.asyncio
async def test_list_featured_cases(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a featured and a non-featured case
    await client.post("/api/v1/cases/", json={
        "title": "Featured Case", "images": ["url1"],
        "category_tags": [], "style_tags": [],
        "is_featured": True,
    }, headers=headers)
    await client.post("/api/v1/cases/", json={
        "title": "Normal Case", "images": ["url2"],
        "category_tags": [], "style_tags": [],
        "is_featured": False,
    }, headers=headers)

    resp = await client.get("/api/v1/cases/featured")
    assert resp.status_code == 200
    featured = resp.json()["data"]
    assert len(featured) >= 1
    titles = [c["title"] for c in featured]
    assert "Featured Case" in titles
    assert "Normal Case" not in titles


@pytest.mark.asyncio
async def test_list_cases_with_filter(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/cases/", json={
        "title": "ins风格母婴店", "images": ["url"],
        "category_tags": ["母婴生活馆"], "style_tags": ["ins风"],
        "store_area_range": "50-100㎡",
    }, headers=headers)
    await client.post("/api/v1/cases/", json={
        "title": "原木风格儿童乐园", "images": ["url"],
        "category_tags": ["儿童乐园"], "style_tags": ["自然原木"],
        "store_area_range": "200㎡+",
    }, headers=headers)

    # Filter by style
    resp = await client.get("/api/v1/cases/?style=ins风")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
    assert all("ins风" in c["style_tags"] for c in items)

    # Filter by area
    resp = await client.get("/api/v1/cases/?area=50-100㎡")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_get_case_detail(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/cases/", json={
        "title": "Detail Test", "images": ["img1", "img2"],
        "category_tags": ["儿童乐园"], "style_tags": ["卡通童趣"],
        "description": "这是一个测试案例",
    }, headers=headers)
    case_id = resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/cases/{case_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "Detail Test"
    assert data["description"] == "这是一个测试案例"
    assert len(data["images"]) == 2


@pytest.mark.asyncio
async def test_update_case(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/cases/", json={
        "title": "Before Update", "images": ["url"],
        "category_tags": [], "style_tags": [],
    }, headers=headers)
    case_id = resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/cases/{case_id}", json={
        "title": "After Update", "is_featured": True,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "After Update"
    assert data["is_featured"] == True


@pytest.mark.asyncio
async def test_delete_case(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/cases/", json={
        "title": "To Be Deleted", "images": ["url"],
        "category_tags": [], "style_tags": [],
    }, headers=headers)
    case_id = resp.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/cases/{case_id}", headers=headers)
    assert resp.status_code == 200

    # Verify deleted
    resp = await client.get(f"/api/v1/cases/{case_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_case_requires_admin(client: AsyncClient):
    resp = await client.post("/api/v1/cases/", json={
        "title": "Unauthorized", "images": ["url"],
        "category_tags": [], "style_tags": [],
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient):
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/cases/", json={
        "title": "Tag Test 1", "images": ["url"],
        "category_tags": ["婴童游泳馆", "母婴生活馆"],
        "style_tags": ["ins风"],
        "store_area_range": "100-200㎡",
    }, headers=headers)
    await client.post("/api/v1/cases/", json={
        "title": "Tag Test 2", "images": ["url"],
        "category_tags": ["儿童乐园"],
        "style_tags": ["卡通童趣", "自然原木"],
        "store_area_range": "200㎡+",
    }, headers=headers)

    resp = await client.get("/api/v1/cases/tags")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["category_tags"]) >= 2
    assert len(data["style_tags"]) >= 3
    assert len(data["area_ranges"]) >= 2


@pytest.mark.asyncio
async def test_list_cases_envelope_fields(client: AsyncClient):
    """锁住分页信封的字段名。

    前端 api/cases.ts 的 CaseListResult 直接采用 api/types.ts 的 Paginated<T>
    （items/total/page/page_size）。这里把同一份契约钉在后端侧：前端任何一层
    把 items 写成别的名字（曾经写成 list），都会让案例列表对真实响应不可用，
    而前端测试全部 mock 掉 ../request，看不见这件事。
    """
    resp = await client.get("/api/v1/cases/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data.keys()) == {"items", "total", "page", "page_size"}
    assert "list" not in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_cases_style_filter_matches_multi_tag_arrays(client: AsyncClient):
    """多标签数组里的标签必须筛得到——目标标签不在数组第一个也一样。

    旧的 JSON.contains([x]) 在通用 JSON 列上退化成子串 LIKE，模式是 ["x"]，
    只对「恰好是单元素数组」的记录成立，所以多标签记录永远筛不到。
    """
    token = await login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/cases/", json={
        "title": "多标签-目标在最后", "images": ["url"],
        "category_tags": ["儿童房", "游戏区"], "style_tags": ["自然原木", "ins风"],
        "store_area_range": "50-100㎡",
    }, headers=headers)
    await client.post("/api/v1/cases/", json={
        "title": "单标签", "images": ["url"],
        "category_tags": ["游戏区"], "style_tags": ["ins风"],
        "store_area_range": "50-100㎡",
    }, headers=headers)
    await client.post("/api/v1/cases/", json={
        "title": "不含目标标签", "images": ["url"],
        "category_tags": ["游戏区"], "style_tags": ["自然原木"],
        "store_area_range": "50-100㎡",
    }, headers=headers)

    resp = await client.get("/api/v1/cases/?style=ins风&page_size=100")
    assert resp.status_code == 200
    data = resp.json()["data"]
    titles = [c["title"] for c in data["items"]]
    assert "多标签-目标在最后" in titles
    assert "单标签" in titles
    assert "不含目标标签" not in titles
    assert all("ins风" in c["style_tags"] for c in data["items"])

    # total 必须是「筛选后」的条数，否则前端分页会以为还有下一页
    assert data["total"] == len(titles)

    # 类型标签同理：目标不在第一个也要筛得到
    resp = await client.get("/api/v1/cases/?category_tag=儿童房&page_size=100")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(c["title"] == "多标签-目标在最后" for c in items)
