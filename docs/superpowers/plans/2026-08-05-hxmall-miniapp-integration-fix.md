# HXMall 小程序端联调修复与功能补齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通 HXMall 微信小程序端到端主链路（微信登录→浏览→详情→加购→下单→订单操作），并补齐购物车与"我的"中心全部页面，后端补齐缺失能力。

**Architecture:** 后端 FastAPI 为契约基准，前端 API 层类型/路径/字段直接对齐后端（方案 B，无 adapter 层）。新增后端能力：wx-login（含开发模式）、商品 hot/new/sort、订单 cancel/confirm/refund、购物车/地址簿/浏览记录/收藏/企业资料。前端新增 10 个页面，购物车/地址簿/浏览记录/收藏全走后端同步。

**Tech Stack:** 后端 FastAPI 0.115 + SQLAlchemy 2.0 async + Alembic + pytest(pytest-asyncio)。前端 uni-app (Vue3) + Pinia + TypeScript + vite/vue-tsc。

## Global Constraints

- 对齐基准：**后端现有 FastAPI 路由与 Pydantic schema 是唯一事实来源**，前端只改不定义新契约。
- 前端适配方式：**B 直接对齐**——`src/api/*.ts` 类型改为后端形状，页面逐处改字段名，不引入 adapter 层。
- 域名：统一 `https://baby.mx.yn.cn/api/v1`（REST）、`wss://baby.mx.yn.cn`（WS）。`request.ts`/`upload.ts` 的 BASE_URL 从 `utils/constants.ts` 的 `API_BASE_URL` 引用。
- **TDD 门禁（用户强制）**：后端每个任务先写 pytest 失败用例→跑失败→最小实现→跑通过。前端无既有测试框架，**验证门禁 = `vue-tsc` 类型检查通过 + `npm run build:mp-weixin` 构建成功**；纯逻辑（订单状态映射、pricing_rules 解析）必须写 vitest 用例（Phase B 先搭 vitest）。测试不通过不进入实现。
- 审核门禁：`place_order` 校验 `user.status == active`，否则 403「账号审核中，暂不能下单」。
- 新用户审核：wx-login 自动建零售商账号 `status=pending_review`。
- 开发模式：`WECHAT_APPID` 为空或 code 以 `dev_` 开头时不调微信，签发测试 token。
- 金额单位：后端 `total_amount` 为「分」，前端展示统一 `/100`。
- 订单状态：前端 `ORDER_STATUS` 常量改为**字符串键**。
- 项目当前**非 git 仓库**：Task A0 先 `git init` + 首次提交；此后每任务末 commit。
- 后端测试库：pytest 用临时 SQLite（`Base.metadata.create_all` 建表），不依赖 alembic，规避枚举变更跨库差异。

---

## Task A0: 初始化 git 仓库

**Files:**
- Create: `backend/.gitignore`、`miniapp/.gitignore`、`.gitignore`
- Modify: 无

**Interfaces:**
- Produces: git 仓库，后续所有任务可 commit

- [ ] **Step 1: 写根 .gitignore**
  忽略 `node_modules/`、`dist/`、`*.pyc`、`__pycache__/`、`.pytest_cache/`、`.env`、`uploads/`、`*.db`、`admin/dist`、`*.tar.gz`。

- [ ] **Step 2: 初始化并首次提交**
  Run: `git init`、`git add -A`、`git commit -m "chore: init repo"`

- [ ] **Step 3: 验证**
  Run: `git status` → Expected: clean，无未跟踪文件（重要业务文件未被忽略）。

---

# Phase A — 后端补齐（TDD，pytest 全绿）

## Task A1: 数据库模型扩展 + 迁移

**Files:**
- Modify: `backend/app/models/user.py`（users 加 nickname/avatar）
- Modify: `backend/app/models/product.py`（products 加 sales_count）
- Create: `backend/app/models/cart.py`、`backend/app/models/address.py`、`backend/app/models/history.py`、`backend/app/models/favorite.py`
- Modify: `backend/app/models/order.py`（OrderStatus 加 REFUNDING）
- Modify: `backend/app/models/__init__.py`（导出新模型）
- Create: `backend/alembic/versions/xxxx_add_cart_address_history_favorites.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces:
  - `CartItem(user_id: Uuid, product_id: Uuid, spec: str = "默认", quantity: int)`，`UniqueConstraint(user_id, product_id, spec)`
  - `Address(user_id, name, phone, province, city, district, detail, is_default: bool)`，索引 user_id
  - `BrowseHistory(user_id, product_id, viewed_at)`，`UniqueConstraint(user_id, product_id)`
  - `Favorite(user_id, product_id, created_at)`，`UniqueConstraint(user_id, product_id)`
  - `User.nickname: str|None`、`User.avatar: str|None`
  - `Product.sales_count: int = 0`
  - `OrderStatus.REFUNDING = "refunding"`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_models.py
import pytest, uuid
from app.models.cart import CartItem
from app.models.address import Address
from app.models.history import BrowseHistory
from app.models.favorite import Favorite
from app.models.user import User
from app.models.product import Product, ProductStatus
from app.models.order import OrderStatus

@pytest.mark.asyncio
async def test_new_models_insert_and_enum_value(db_session):
    u = User(phone="13900000001", hashed_password="x")
    db_session.add(u); await db_session.flush()
    db_session.add(CartItem(user_id=u.id, product_id=uuid.uuid4(), quantity=5))
    db_session.add(Address(user_id=u.id, name="张三", phone="13900000001",
                           province="省", city="市", district="区", detail="路1号"))
    db_session.add(BrowseHistory(user_id=u.id, product_id=uuid.uuid4()))
    db_session.add(Favorite(user_id=u.id, product_id=uuid.uuid4()))
    p = Product(name="测试商品", pricing_rules={"normal": [{"qty": 10, "price": 1.0}]},
                status=ProductStatus.ON_SALE)
    db_session.add(p)
    await db_session.flush()
    assert OrderStatus.REFUNDING == "refunding"
    assert p.sales_count == 0
    assert u.nickname is None
```

- [ ] **Step 2: 运行确认失败**
  Run: `cd backend && pytest tests/test_models.py -v`
  Expected: FAIL（ModuleNotFoundError: cart / Column 不存在）。

- [ ] **Step 3: 最小实现——新增模型文件**
  按 `models/product.py` 既有风格写 4 个模型（`Base`/`TimestampMixin`、`Mapped/mapped_column`、`Uuid` 主键用 `uuid.uuid4` default、`UniqueConstraint`）。`User` 加 `nickname`/`avatar` 列；`Product` 加 `sales_count` 列；`OrderStatus` 加 `REFUNDING` 成员。

- [ ] **Step 4: 更新 `models/__init__.py` 导出**

```python
from app.models.cart import CartItem
from app.models.address import Address
from app.models.history import BrowseHistory
from app.models.favorite import Favorite
```

- [ ] **Step 5: 迁移（alembic 手写 1 个版本文件）**
  合并为单迁移：`op.add_column('products', sales_count)`、`op.add_column('users', nickname)`、`op.add_column('users', avatar)`、建 4 张新表。Postgres 枚举加值用：
  ```python
  op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'refunding'")
  ```
  （SQLite 测试库不跑 alembic，故无需兼容。）

- [ ] **Step 6: 跑测试通过**
  Run: `pytest tests/test_models.py -v`
  Expected: PASS。

- [ ] **Step 7: Commit**
  `git add -A && git commit -m "feat(models): cart/address/history/favorite models, nickname/avatar, sales_count, refunding"`

> **pytest fixture 说明**（后续所有后端任务沿用）：`backend/tests/conftest.py` **已存在**，提供 `client`（ASGI httpx）与 `db_session` 两个 fixture，用内存 SQLite + `Base.metadata.create_all/drop_all` 建删表，无需 alembic。新模型只要导入 `app.models` 即自动建表，`OrderStatus.REFUNDING` 等枚举变更也随之生效。所有新测试沿用这两个 fixture，不新增基础设施。

---

## Task A2: 微信登录 + 审核门禁

**Files:**
- Modify: `backend/app/api/auth.py`（加 `/wx-login`）
- Modify: `backend/app/schemas/user.py`（`UserOut` 加 nickname/avatar；加 `WxLoginRequest`、`WxLoginResult`）
- Modify: `backend/app/config.py`（确认 WECHAT_APPID/SECRET 已存在，加 `WX_DEV_CODE_PREFIX: str = "dev_"`）
- Modify: `backend/app/api/orders.py`（`place_order` 加审核门禁）
- Test: `backend/tests/test_wx_login.py`、`backend/tests/test_order_gate.py`

**Interfaces:**
- Consumes: `auth_service.create_access_token/create_refresh_token`、`hash_password`
- Produces:
  - `POST /api/v1/auth/wx-login` body `{"code": str, "user_info": {nickName?, avatarUrl?} | None}` → `APIResponse[{"access_token","refresh_token","user_info": UserOut}]`
  - `GET /api/v1/users/me` 现在返回含 nickname/avatar 的 UserOut

- [ ] **Step 1: 写失败测试 `tests/test_wx_login.py`**

```python
import uuid, pytest
from app.models.user import UserStatus
from app.models.product import Product, ProductStatus

@pytest.mark.asyncio
async def test_wx_login_dev_mode_creates_pending_review_user(client, db_session):
    res = await client.post("/api/v1/auth/wx-login",
        json={"code": "dev_abc123", "user_info": {"nickName": "测试"}})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["access_token"] and data["refresh_token"]
    assert data["user_info"]["status"] == "pending_review"
    assert data["user_info"]["nickname"] == "测试"

@pytest.mark.asyncio
async def test_wx_login_same_code_same_user(client, db_session):
    r1 = await client.post("/api/v1/auth/wx-login", json={"code": "dev_dup"})
    r2 = await client.post("/api/v1/auth/wx-login", json={"code": "dev_dup"})
    assert r1.json()["data"]["user_info"]["id"] == r2.json()["data"]["user_info"]["id"]

@pytest.mark.asyncio
async def test_order_gate_rejects_pending_review(client, db_session):
    # 造一个 on_sale 商品
    p = Product(name="泳圈", pricing_rules={"normal": [{"qty": 10, "price": 35.0}]},
                status=ProductStatus.ON_SALE, min_order_qty=10, stock=100)
    db_session.add(p); await db_session.flush()
    # register 建 pending_review 用户并登录
    await client.post("/api/v1/auth/register", json={
        "phone": "13900000002", "password": "pass1234",
        "company_name": "测试公司", "business_license": "BL1", "contact_person": "李四"})
    login = await client.post("/api/v1/auth/login",
        json={"phone": "13900000002", "password": "pass1234"})
    token = login.json()["data"]["access_token"]
    # 未审核用户下单应 403
    res = await client.post("/api/v1/orders", json={
        "items": [{"product_id": str(p.id), "name": "泳圈", "qty": 10,
                   "unit_price": 35.0, "subtotal": 350.0}],
        "payment_method": "wechat_pay"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
```

- [ ] **Step 2: 运行确认失败**
  Run: `pytest tests/test_wx_login.py tests/test_order_gate.py -v` → FAIL（404/无端点）。

- [ ] **Step 3: 实现 `/auth/wx-login`**
  - 读 `settings.WECHAT_APPID`；为空或 `code.startswith("dev_")` → `openid = "dev_" + code`；
  - 否则用 `httpx` 调 `https://api.weixin.qq.com/sns/jscode2session?appid=..&secret=..&js_code=..&grant_type=authorization_code`，解析 `openid`；`errcode` 非 0 抛 401。
  - 按 `wx_openid` 查 `User`；无则创建 `role=RETAILER, level=NORMAL, status=PENDING_REVIEW`，`nickname/avatar` 取 `user_info`。
  - 返回 tokens + `UserOut`。

- [ ] **Step 4: 实现审核门禁**
  `orders.py::place_order` 内、`create_order` 调用前：查询 `User.status`，非 ACTIVE 且角色非 admin/operator → `HTTPException(403, "账号审核中，暂不能下单")`。

- [ ] **Step 5: 跑测试通过** → PASS。

- [ ] **Step 6: Commit**
  `git commit -am "feat(auth): wx-login with dev mode, order gate pending_review"`

---

## Task A3: 商品 hot / new / sort

**Files:**
- Modify: `backend/app/api/products.py`
- Test: `backend/tests/test_products_sort.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/products/hot?limit=10` → `APIResponse[list[ProductListOut]]`（on_sale，sales_count desc）
  - `GET /api/v1/products/new?limit=10` → `APIResponse[list[ProductListOut]]`（on_sale，created_at desc）
  - `GET /api/v1/products?sort=newest|sales_desc|price_asc|price_desc`（默认 newest）

- [ ] **Step 1: 写失败测试**（造 3 个 on_sale 商品，不同 sales_count / 价格档 / created_at，断言排序与 hot/new 集合）。
- [ ] **Step 2: 运行确认失败** → 404/参数不支持。
- [ ] **Step 3: 实现**
  - `/hot`、`/new`：`select(Product).where(Product.status==ProductStatus.ON_SALE).order_by(Product.sales_count.desc()).limit(limit)`（`/new` 用 `Product.created_at.desc()`），转 `ProductListOut`（复用 `get_price_range`）。
  - `/` 增加 `sort: str = Query("newest")`：`newest`→created_at desc；`sales_desc`→sales_count desc；`price_asc|price_desc`→查出候选后按 `get_price_range` 的 min 内存排序（限定 top 200 后再 offset/limit，分页精度以说明为准）。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(products): hot/new endpoints and sort param"`

---

## Task A4: 订单 cancel / confirm / refund

**Files:**
- Modify: `backend/app/api/orders.py`、`backend/app/schemas/order.py`
- Test: `backend/tests/test_order_actions.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/orders/{id}/cancel`（本人 + pending_payment → cancelled）
  - `POST /api/v1/orders/{id}/confirm`（本人 + shipped → completed）
  - `POST /api/v1/orders/{id}/refund`（本人 + paid|shipped → refunding）
  - `OrderStatusUpdate.status` pattern 扩为 `^(paid|shipped|confirmed|completed|cancelled|refunding)$`

- [ ] **Step 1: 写失败测试**：下单→cancel 成功；越权 403；非 pending_payment cancel 400；shipped→confirm→completed；paid→refund→refunding。
- [ ] **Step 2: 运行确认失败** → 404。
- [ ] **Step 3: 实现三个端点**（模式同 `submit_payment`：校验本人、校验前置状态、改 `order.status`、追加 timeline、`flag_modified`）。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(orders): cancel/confirm/refund endpoints"`

---

## Task A5: 购物车后端

**Files:**
- Create: `backend/app/api/cart.py`；Modify: `backend/app/api/__init__.py`（挂载 `/cart`）
- Test: `backend/tests/test_cart_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/cart` → `APIResponse[list[CartItemOut]]`，`CartItemOut{id, product_id, name, image, spec, quantity, unit_price_min, unit_price_max, stock, min_order_qty}`
  - `POST /api/v1/cart` body `{product_id, spec?, quantity}` → 已存在则累加数量
  - `PUT /api/v1/cart/{id}` body `{quantity}`（>0）
  - `DELETE /api/v1/cart/{id}`、`DELETE /api/v1/cart`（清空）

- [ ] **Step 1: 写失败测试**：加购（新/累加）、改量、删除、清空、越权（他人购物车项 404/403）。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**（联表 `Product` 取 name/image/stock/min_order_qty，价格区间 `get_price_range`）。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(cart): cart CRUD backend"`

---

## Task A6: 地址簿后端

**Files:**
- Create: `backend/app/api/addresses.py`；Modify: `backend/app/api/__init__.py`（挂载 `/users/addresses`，prefix 用 `/users`）
- Test: `backend/tests/test_address_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/users/addresses` → list（默认地址置顶）
  - `POST /api/v1/users/addresses` body `{name, phone, province, city, district, detail, is_default?}`；若 is_default 则清其余默认
  - `PUT /api/v1/users/addresses/{id}`、`DELETE /api/v1/users/addresses/{id}`（仅本人）

- [ ] **Step 1: 写失败测试**：CRUD、默认地址唯一、越权。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(address): address book CRUD"`

---

## Task A7: 浏览记录后端

**Files:**
- Create: `backend/app/api/history.py`；Modify: `backend/app/api/__init__.py`（挂载 `/history`）
- Test: `backend/tests/test_history_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/history?page&page_size` → `PaginatedResponse[HistoryItemOut{product_id, name, image, price_min, price_max, viewed_at}]`
  - `POST /api/v1/history` body `{product_id}`（upsert：已存在则更新 viewed_at）
  - `DELETE /api/v1/history/{product_id}`、`DELETE /api/v1/history`（清空）

- [ ] **Step 1: 写失败测试**：记录、重复记录更新时间、分页倒序、删除。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**（联表 Product）。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(history): browse history backend"`

---

## Task A8: 收藏后端

**Files:**
- Create: `backend/app/api/favorites.py`；Modify: `backend/app/api/__init__.py`（挂载 `/favorites`）
- Test: `backend/tests/test_favorites_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/favorites?page&page_size` → `PaginatedResponse[FavoriteItemOut{product_id, name, image, price_min, price_max, created_at}]`
  - `POST /api/v1/favorites` body `{product_id}`（幂等）
  - `DELETE /api/v1/favorites/{product_id}`

- [ ] **Step 1: 写失败测试**：收藏、重复幂等、列表、取消。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(favorites): favorites CRUD"`

---

## Task A9: 企业资料更新

**Files:**
- Modify: `backend/app/api/users.py`（加 `PUT /users/me/profile`）
- Modify: `backend/app/schemas/user.py`（加 `RetailerProfileUpdate`）
- Test: `backend/tests/test_profile_api.py`

**Interfaces:**
- Produces:
  - `PUT /api/v1/users/me/profile` body `{company_name?, business_license?, contact_person?}`（仅零售商）→ 更新 `RetailerProfile`，返回 UserOut

- [ ] **Step 1: 写失败测试**：更新成功、非零售商 403、字段可选。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**（查 retailer_profile，缺失则创建）。
- [ ] **Step 4: 跑测试通过**。
- [ ] **Step 5: Commit** `git commit -am "feat(profile): retailer profile update"`

**Phase A 完成门禁**：Run `cd backend && pytest -v` → 全绿。`alembic upgrade head`（Postgres）无报错。

---

# Phase B — 前端 API 层对齐 + 登录 + 商品/首页

> 前端验证门禁：每任务末尾 `npx vue-tsc --noEmit` 通过 + `npm run build:mp-weixin` 成功。逻辑代码附 vitest 用例（Task B0 搭建）。

## Task B0: 搭建前端 vitest

**Files:**
- Create: `miniapp/vitest.config.ts`、`miniapp/src/utils/__tests__/mapping.test.ts`
- Modify: `miniapp/package.json`（加 vitest devDep + `"test": "vitest run"`）

- [ ] **Step 1: 写失败测试** `mapping.test.ts`：`orderStatusLabel("paid") === "待发货"`、`formatCents(3500) === "¥35.00"`。
- [ ] **Step 2: 运行确认失败**（`orderStatusLabel`/`formatCents` 不存在）。
- [ ] **Step 3: 实现**：`utils/constants.ts` 改字符串键 + 新增 `utils/mapping.ts`（`orderStatusLabel`、`orderStatusColor`、`formatCents`、`parsePriceRange(pricing_rules)`）。
- [ ] **Step 4: 跑通过** `npm test`。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): vitest setup + status/cents mapping utils"`

## Task B1: request/constants 接线 + API 层对齐

**Files:**
- Modify: `miniapp/src/api/request.ts`、`miniapp/src/api/upload.ts`、`miniapp/src/utils/constants.ts`
- Modify: `miniapp/src/api/products.ts`、`miniapp/src/api/orders.ts`、`miniapp/src/api/auth.ts`
- Create: `miniapp/src/api/cart.ts`、`miniapp/src/api/address.ts`、`miniapp/src/api/history.ts`、`miniapp/src/api/favorites.ts`

**Interfaces:**
- Produces（类型全部对齐后端）：
  - `Product{id, name, images[], description?, specs?: Record<string,string[]>, age_range?, safety_certifications?: {name,icon}[], stock?, min_order_qty, pricing_rules: Record<string,{qty,price}[]>, status, category?: {id,name,icon}}`
  - `Order{id, order_no, type, status: string, items: {product_id,name,qty,unit_price,subtotal,image?}[], total_amount: number(分), payment_method?, payment_status, receiver_name?, receiver_phone?, receiver_address?, remark?, timeline?, created_at?}`
  - `createOrder(params: {items, payment_method, remark?, receiver_name?, receiver_phone?, receiver_address?})`
  - `wxLogin({code, user_info?})`、`getUserProfile()` → `/users/me`
  - `getCategories()` → `/products/categories`；`getHotProducts/getNewProducts` → `/products/hot|/products/new`
  - `cart.ts/address.ts/history.ts/favorites.ts` 方法名映射 A5–A8 端点

- [ ] **Step 1: 写失败测试**：`request.ts` 的 `BASE_URL === API_BASE_URL`（vitest 断言）。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**：request/upload 引用 `API_BASE_URL`；重写 products/orders/auth 类型与路径；新建 4 个 API 文件。
- [ ] **Step 4: 门禁验证**：`vue-tsc --noEmit` + `npm test` + `build:mp-weixin`。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): api layer aligned to backend contract"`

## Task B2: 登录接入

**Files:**
- Modify: `miniapp/src/stores/user.ts`、`miniapp/src/pages/mine/index.vue`
- Test: `miniapp/src/stores/__tests__/user.test.ts`

- [ ] **Step 1: 写失败测试**：`login()` 调用 `wxLogin`（mock `uni.login` + api）后写入 token 与 userInfo。
- [ ] **Step 2: 运行确认失败**（当前 mock）。
- [ ] **Step 3: 实现**：user store `login()` 改真实 `uni.login`→`wxLogin`；`fetchUserInfo` 调 `getUserProfile`；mine 页"点击登录"接 `handleLogin`（去 mock 确认框）。
- [ ] **Step 4: 门禁验证** + 手动：dev 模式登录成功、我的页显示信息。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): real wechat login flow"`

## Task B3: 商品/首页改造

**Files:**
- Modify: `miniapp/src/pages/products/index.vue`、`miniapp/src/pages/products/detail.vue`、`miniapp/src/pages/home/index.vue`
- Test: `miniapp/src/utils/__tests__/mapping.test.ts` 追加 `parsePriceRange` 用例

- [ ] **Step 1: 写失败测试**：`parsePriceRange({normal:[{qty:10,price:30},{qty:100,price:25}]})` → `{min:25, max:30}`。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**
  - home：分类→`getCategories`（已对齐 `/products/categories`）；推荐→`getNewProducts`；热门→`getHotProducts`；banner 用 hot 数据。购物车角标**暂保持读本地 cart**（`cartStore.totalCount`），待 C1 购物车 store 后端同步时改读后端。
  - products/index：字段改名（`moq`→`min_order_qty`）、传 `sort`。
  - products/detail：价格区间/批发价表从 `pricing_rules` 渲染（用 `parsePriceRange` + 按用户等级取档）；`unit` 缺省"件"；`sales_count` 用新字段；打开时 `POST /history`；收藏按钮接 `favorites.ts`（已收藏态用 `GET /favorites` 查交集或本页维护）。
- [ ] **Step 4: 门禁验证**（vue-tsc + npm test + build）。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): products/home aligned + history/favorite hooks"`

---

# Phase C — 下单链路

## Task C1: 购物车 store 后端同步

**Files:**
- Modify: `miniapp/src/stores/cart.ts`
- Test: `miniapp/src/stores/__tests__/cart.test.ts`

- [ ] **Step 1: 写失败测试**：`fetch()` 从 `/cart` 填充 items；`addItem` 调 `POST /cart` 并刷新；未登录时 `fetch` 置空。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**：cart store 的方法改为调 `api/cart.ts`；保留 `checked` 本地 UI 态；`getCheckoutItems` 返回后端项；把首页与商品详情的购物车角标改为读后端购物车数量（登录后 `cartStore.fetch()` 后取 `totalCount`）。
- [ ] **Step 4: 门禁验证**。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): cart store backend sync"`

## Task C2: 结算页改造

**Files:**
- Modify: `miniapp/src/pages/order/checkout.vue`
- Test: `miniapp/src/utils/__tests__/mapping.test.ts` 追加 `formatCents` 已有；补 `buildOrderItems(checkoutItems)` 纯函数测试

- [ ] **Step 1: 写失败测试**：`buildOrderItems(items)` → 映射为 `{product_id, name, qty, unit_price, subtotal, image?}`。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**：结算项从后端购物车选中项构建；地址从 `api/address.ts` 拉取，选地址后填 `receiver_name/phone/address`；`createOrder` 传后端形状；支付方式 `wechat_pay`（保留 bank_transfer + 上传凭证）；金额 `/100`。
- [ ] **Step 4: 门禁验证** + 手动：dev 登录→下单成功。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): checkout aligned to backend order contract"`

## Task C3: 订单列表/详情改造

**Files:**
- Modify: `miniapp/src/pages/order/list.vue`、`miniapp/src/pages/order/detail.vue`、`miniapp/src/utils/constants.ts`

- [ ] **Step 1: 写失败测试**：`orderStatusLabel`/`orderStatusColor` 覆盖全部 7 个字符串状态；`formatCents`。
- [ ] **Step 2: 运行确认失败**。
- [ ] **Step 3: 实现**：列表/详情用字符串状态映射（`mapping.ts`）；金额 `formatCents`；items 后端结构；操作按钮：待付款→取消、已发货→确认收货、已发货/已付款→退款；调 C 端新端点。
- [ ] **Step 4: 门禁验证** + 手动：状态流转正确。
- [ ] **Step 5: Commit** `git commit -am "feat(frontend): order list/detail aligned + actions"`

---

# Phase D — 页面补齐

> 全部新页面按既有视觉体系（#FF7B7B 主题、圆角卡片、loading/empty/error 四态）。每任务末尾门禁验证。

## Task D1: 购物车页 `pages/cart/index.vue`

**Files:** Create: `miniapp/src/pages/cart/index.vue`；Modify: `miniapp/src/pages.json`
- checkbox 全选/单选、步进改量（调 `PUT /cart/{id}`）、删除（`DELETE`）、合计（`formatCents`）、去结算（`switchTab` 或 navigateTo checkout）、未登录引导登录。
- 注册到 pages.json。

## Task D2: 企业信息页 `pages/mine/company/index.vue`
- 表单（公司名/营业执照号/联系人）→ `PUT /users/me/profile`；提交后提示待审核。

## Task D3: 地址簿页 `pages/mine/address/index.vue`
- 列表/新增/编辑/删除/设默认 → `api/address.ts`。

## Task D4: 会员中心页 `pages/mine/member/index.vue`
- 展示等级/折扣/账期额度（`credit_limit`/`credit_balance` 分→元）/购买画像摘要（`retailer_profile`）。

## Task D5: 收藏页 `pages/mine/favorites/index.vue`
- 列表 + 取消收藏 → `api/favorites.ts`。

## Task D6: 浏览记录页 `pages/mine/history/index.vue`
- 列表 + 清空 → `api/history.ts`。

## Task D7: 优惠券页 `pages/mine/coupons/index.vue`（只读占位）
- 占位文案 + 预留 `TODO` 数据源接入点（第三方后续对接），不做领取/核销。

## Task D8: 客服/设置/帮助页
- `pages/mine/contact/index.vue`：客服电话/微信展示。
- `pages/mine/settings/index.vue`：清缓存（`clearStorage`）、关于版本、退出登录。
- `pages/mine/help/index.vue`：静态 FAQ。

## Task D9: pages.json 注册 + 全量验证

**Files:** Modify: `miniapp/src/pages.json`
- [ ] **Step 1**：确认 D1–D8 全部页面路径已注册（含 `mine/*` 的 navigationBarTitleText 与主题色）。
- [ ] **Step 2**：全量门禁：`vue-tsc --noEmit` + `npm test` + `npm run build:mp-weixin` 成功。
- [ ] **Step 3**：跑完整手动验证清单（§7），修正发现的问题。
- [ ] **Step 4**：Commit `git commit -am "feat(frontend): register all pages + full build verified"`

---

## Self-Review（计划内嵌）

**Spec 覆盖核对**：§5.1→A2；§5.2→A3；§5.3→A4；§5.4→A5–A9；§5.5→A1；§5.6→各任务测试；§6.1→B1；§6.2→B3/C2/C3/D1–D8；§6.3→B2/C1；§6.4→B0/B1/D9。无遗漏。

**手动验证清单（最终验收）**
1. 登录（dev 模式）→ 我的页显示用户信息
2. 首页分类/推荐/热门/轮播加载正常
3. 商品详情价格/批发价表/规格/起订量正确；收藏生效；打开即记浏览
4. 加购 → 购物车页管理 → 结算选地址 → 下单成功
5. 订单：待付款取消 / 已发货确认收货 / 退款流转正确
6. 会员中心、企业资料、浏览记录、优惠券占位页、客服/设置/帮助可访问
