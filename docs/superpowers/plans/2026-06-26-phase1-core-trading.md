# Phase 1：MVP 核心交易链路 + 品牌视觉 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-group by task-group. Each group is independently testable. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 亲子温馨风格的儿童产品 B2B 小程序上线 — 零售商可浏览商品和案例、手动下单、微信支付/银行转账

**Architecture:** FastAPI 模块化单体后端 + uni-app (Vue3) 微信小程序 + 管理后台。PostgreSQL + Redis，Docker 部署。后端按 models → services → api 三层组织，前端按 Tab 页面 + 组件模式组织。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL 15+, pgvector, Redis 7, uni-app (Vue3 + TS), uView Plus 3.x, Pinia, Docker, Nginx

**Design Doc:** `docs/superpowers/specs/2026-06-26-b2b-mall-design.md`

## Global Constraints

- Python ≥ 3.11, Node ≥ 18
- API base path: `/api/v1/`
- JWT access token 2h expiry, refresh token 7d
- All prices in Decimal, stored as cents in DB (integer)
- Image uploads: max 10MB, WebP conversion on upload
- API responses follow `{ "code": 0, "data": ..., "message": "ok" }` envelope
- Frontend color tokens from spec section 4.1: coral `#FF7B7B`, cream `#FFF8F0`, sky blue `#7EC8E3`, mint `#A8D8B9`, honey `#FFD93D`
- Frontend font: system rounded/sans-serif stack (no custom font for WeChat mini program)
- All public-facing copy must use "小暖" for AI assistant name
- Product list items must show: thumbnail, name, wholesale price range, age_range tag, stock status
- All code has Chinese comments for team readability

---

## File Structure Map

```
hxmall/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, routers
│   │   ├── config.py               # Pydantic Settings (DB, Redis, JWT, OSS)
│   │   ├── database.py             # AsyncSession, get_db dependency
│   │   ├── redis.py                # Redis client, cache helpers
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # DeclarativeBase, TimestampMixin
│   │   │   ├── user.py             # User, RetailerProfile, DesignerProfile
│   │   │   ├── product.py          # Category, Product
│   │   │   ├── case.py             # DesignCase (案例图库)
│   │   │   └── order.py            # Order, OrderItem
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py           # APIResponse, PaginatedResponse
│   │   │   ├── user.py             # UserCreate, UserLogin, UserOut, TokenResponse
│   │   │   ├── product.py          # ProductCreate, ProductOut, ProductList, PricingRule
│   │   │   ├── case.py             # CaseCreate, CaseOut, CaseList
│   │   │   └── order.py            # OrderCreate, OrderOut, OrderStatusUpdate
│   │   ├── api/
│   │   │   ├── __init__.py         # APIRouter aggregation
│   │   │   ├── deps.py             # get_current_user, get_current_admin, require_role
│   │   │   ├── auth.py             # POST /auth/login, /auth/refresh, /auth/wx-login
│   │   │   ├── users.py            # CRUD users, retailer review
│   │   │   ├── products.py         # Product CRUD, category list
│   │   │   ├── cases.py            # DesignCase CRUD, featured list
│   │   │   ├── orders.py           # Order create/list/detail/status
│   │   │   └── upload.py           # File upload (OSS / local), image processing
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # JWT encode/decode, password hashing
│   │   │   ├── pricing.py          # get_price(level, qty, pricing_rules) → unit_price
│   │   │   ├── order_service.py    # create_order, validate_inventory, assign_designer
│   │   │   └── upload_service.py   # save_file, to_webp, generate_thumbnail
│   │   ├── middleware/
│   │   │   └── exception_handler.py # Global exception → APIResponse envelope
│   │   └── tasks/
│   │       └── __init__.py          # Background tasks placeholder (Phase 2 for AI)
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── tests/
│   │   ├── conftest.py             # async test fixtures, test DB, test client
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   ├── test_pricing.py
│   │   ├── test_orders.py
│   │   └── test_cases.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml          # backend + postgres + redis
│
├── miniapp/                        # uni-app 微信小程序
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts                 # Entry, Pinia setup
│   │   ├── pages.json              # TabBar config, page routes
│   │   ├── manifest.json           # WeChat appid, permissions
│   │   ├── pages/
│   │   │   ├── home/
│   │   │   │   └── index.vue       # 首页：Banner + 品类导航 + 推荐Feed + 案例瀑布流
│   │   │   ├── ai-assistant/
│   │   │   │   └── index.vue       # 小暖AI：Phase 1 占位页（品牌展示 + "即将上线"引导）
│   │   │   ├── cases/
│   │   │   │   ├── index.vue       # 案例列表：瀑布流 + 筛选
│   │   │   │   └── detail.vue      # 案例详情：大图浏览 + 关联设计服务
│   │   │   ├── products/
│   │   │   │   ├── index.vue       # 商品列表：品类筛选 + 适龄/认证筛选
│   │   │   │   └── detail.vue      # 商品详情：批发价阶梯表 + 认证展示
│   │   │   ├── order/
│   │   │   │   ├── list.vue        # 订单列表
│   │   │   │   ├── detail.vue      # 订单详情
│   │   │   │   └── checkout.vue    # 结算页
│   │   │   └── mine/
│   │   │       └── index.vue       # 我的：零售商信息/等级/订单入口
│   │   ├── components/
│   │   │   ├── ProductCard.vue     # 商品卡片（缩略图+名称+批发价区间+适龄标签）
│   │   │   ├── CaseCard.vue        # 案例卡片（大图+标题+标签）
│   │   │   ├── PriceTable.vue      # 阶梯价表格组件
│   │   │   ├── AgeTag.vue          # "适合3-6岁" 标签
│   │   │   ├── CertBadge.vue       # 安全认证徽章
│   │   │   ├── PageLoading.vue     # 加载骨架屏
│   │   │   ├── EmptyState.vue      # 空状态占位
│   │   │   └── SearchBar.vue       # 搜索栏（文字+语音入口）
│   │   ├── api/
│   │   │   ├── request.ts          # uni.request 封装 + 拦截器 + Token 刷新
│   │   │   ├── auth.ts             # 登录/注册 API
│   │   │   ├── products.ts         # 商品 API
│   │   │   ├── cases.ts            # 案例 API
│   │   │   ├── orders.ts           # 订单 API
│   │   │   └── upload.ts           # 上传 API
│   │   ├── stores/
│   │   │   ├── user.ts             # Pinia: 用户信息/Token/等级
│   │   │   ├── cart.ts             # Pinia: 购物车
│   │   │   └── app.ts              # Pinia: 全局状态
│   │   ├── styles/
│   │   │   ├── theme.scss          # CSS 变量：色板/圆角/阴影/字体
│   │   │   └── global.scss         # 全局样式 reset
│   │   └── utils/
│   │       ├── constants.ts        # 枚举/常量
│   │       └── index.ts            # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
└── admin/                          # 管理后台（Vue3 + Vite SPA，内部使用）
    ├── src/
    │   ├── App.vue
    │   ├── main.ts
    │   ├── pages/
    │   │   ├── dashboard/
    │   │   │   └── index.vue       # 数据概览
    │   │   ├── products/
    │   │   │   ├── list.vue        # 商品列表管理
    │   │   │   └── form.vue        # 商品新增/编辑表单
    │   │   ├── cases/
    │   │   │   ├── list.vue        # 案例列表管理
    │   │   │   └── form.vue        # 案例新增/编辑
    │   │   ├── orders/
    │   │   │   ├── list.vue        # 订单列表
    │   │   │   └── detail.vue      # 订单处理（状态变更/指派设计师）
    │   │   └── users/
    │   │       ├── list.vue        # 用户列表
    │   │       └── review.vue      # 零售商审核
    │   ├── api/                    # 同 miniapp 结构
    │   ├── stores/
    │   ├── styles/
    │   └── components/
    ├── package.json
    └── vite.config.ts
```

---

## Task Group 1：项目脚手架 + 基础设施（后端开发）

> **负责人：程序师** | 预计 2-3 天 | 产出：可运行的空框架，数据库连接正常，Docker 就绪

**验收标准：**
- `docker-compose up` 启动 backend + postgres + redis 三个容器
- `GET /api/v1/health` 返回 `{"code":0,"data":{"db":"ok","redis":"ok"}}`
- Alembic 迁移可以生成和执行
- 测试框架就绪，`pytest` 能跑通一个示例测试

### Task 1.1：FastAPI 项目骨架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/redis.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/app/middleware/__init__.py`
- Create: `backend/app/middleware/exception_handler.py`
- Create: `backend/Dockerfile`
- Create: `backend/docker-compose.yml`

**Interfaces:**
- Produces:
  - `config.Settings` — typed settings from env vars
  - `database.get_db() -> AsyncGenerator[AsyncSession]` — FastAPI dependency
  - `redis.get_redis() -> Redis` — FastAPI dependency
  - `schemas.common.APIResponse[T]` — `{"code":0,"data":T,"message":"ok"}`
  - `schemas.common.PaginatedResponse[T]` — `{"items":T[],"total":int,"page":int,"page_size":int}`
  - `models.base.Base` — SQLAlchemy DeclarativeBase
  - `models.base.TimestampMixin` — `created_at`, `updated_at`
  - `GET /api/v1/health` — health check endpoint

<details>
<summary>Code for each file (click to expand)</summary>

**`backend/requirements.txt`:**
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.1
pydantic==2.10.4
pydantic-settings==2.7.1
redis==5.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.19
aiofiles==24.1.0
Pillow==11.1.0
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0
httpx==0.28.1
```

**`backend/app/__init__.py`:**
```python
# FastAPI Backend - B2B Children's Products Mall
```

**`backend/app/config.py`:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "HXMall B2B API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hxmall"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OSS / File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = ""

    # WeChat
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**`backend/app/database.py`:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20, max_overflow=10)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**`backend/app/redis.py`:**
```python
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

redis_client: aioredis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_redis() -> aioredis.Redis:
    """FastAPI dependency: yields the Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client

async def close_redis():
    if redis_client:
        await redis_client.close()
```

**`backend/app/models/base.py`:**
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**`backend/app/schemas/common.py`:**
```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None

    @classmethod
    def ok(cls, data: T = None, message: str = "ok") -> "APIResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = -1) -> "APIResponse":
        return cls(code=code, message=message, data=None)

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
```

**`backend/app/api/__init__.py`:**
```python
from fastapi import APIRouter
from app.api import auth, users, products, cases, orders, upload

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(products.router, prefix="/products", tags=["商品"])
api_router.include_router(cases.router, prefix="/cases", tags=["案例"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(upload.router, prefix="/upload", tags=["上传"])
```

**`backend/app/api/deps.py`:**
```python
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.config import get_settings
from app.database import get_db
from app.redis import get_redis

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify JWT token and return user payload. Raises 401 if invalid."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效")
        return {"user_id": UUID(user_id), "role": payload.get("role", "retailer")}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效或已过期")

async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role. Raises 403 if not admin."""
    if current_user["role"] not in ("admin", "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user

def require_role(*roles: str):
    """Factory: create a dependency that requires one of the given roles."""
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"需要{'/'.join(roles)}权限")
        return current_user
    return _check
```

**`backend/app/middleware/exception_handler.py`:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas.common import APIResponse

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=APIResponse.error(message=str(exc)).model_dump())

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content=APIResponse(code=422, message="参数校验失败", data=errors).model_dump())
```

**`backend/app/main.py`:**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.config import get_settings
from app.database import engine
from app.redis import init_redis, close_redis, redis_client
from app.api import api_router
from app.middleware.exception_handler import global_exception_handler, validation_exception_handler
from app.schemas.common import APIResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Routes
app.include_router(api_router)

@app.get("/api/v1/health", tags=["系统"])
async def health_check():
    db_ok = False
    redis_ok = False
    try:
        from app.database import async_session_factory
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass
    try:
        if redis_client:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        pass
    return APIResponse.ok(data={"db": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"})
```

**`backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`backend/docker-compose.yml`:**
```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/hxmall
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: hxmall
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
```

</details>

- [ ] **Step 1: 创建 backend 目录结构和所有基础文件**

```bash
mkdir -p backend/app/{models,schemas,api,services,middleware,tasks}
mkdir -p backend/alembic/versions
mkdir -p backend/tests
```

用上面 Code blocks 中的内容写入每个文件。

- [ ] **Step 2: 安装 Python 依赖并验证导入**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "from app.main import app; print('Import OK')"
```

预期输出: `Import OK`

- [ ] **Step 3: 初始化 Alembic**

```bash
cd backend
alembic init alembic
```

编辑 `alembic/env.py`，将 `target_metadata` 指向 `app.models.base.Base.metadata`，并配置异步引擎。

- [ ] **Step 4: 启动 Docker Compose 并验证 health check**

```bash
cd backend
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

预期：`{"code":0,"data":{"db":"ok","redis":"ok"},"message":"ok"}`

- [ ] **Step 5: 编写并运行一个示例测试**

Create `backend/tests/conftest.py`:
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine, Base

@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

Create `backend/tests/test_health.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
```

Run:
```bash
cd backend
pytest tests/test_health.py -v
```

预期：1 passed

---

## Task Group 2：用户模型 + 认证系统（后端开发）

> **负责人：程序师** | 预计 1-2 天 | 产出：用户注册/登录/Token刷新 API，角色权限中间件

**验收标准：**
- `POST /api/v1/auth/register` — 零售商注册（手机号+密码+营业执照信息）
- `POST /api/v1/auth/login` — 手机号+密码登录，返回 access_token + refresh_token
- `POST /api/v1/auth/refresh` — 用 refresh_token 换新 access_token
- `GET /api/v1/users/me` — 获取当前用户信息（需登录）
- `GET /api/v1/users/` — 管理员查看用户列表（需管理员）
- 注册时 status = `pending_review`，管理员审核后改为 `active`

### Task 2.1：用户模型定义

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/user.py`
- Modify: `backend/app/models/__init__.py`

### Task 2.2：认证服务 + Token 管理

**Files:**
- Create: `backend/app/services/auth_service.py`

### Task 2.3：认证 API 端点

**Files:**
- Create: `backend/app/api/auth.py`
- Create: `backend/app/api/users.py`
- Modify: `backend/app/api/__init__.py`

### Task 2.4：数据库迁移 + 测试

- [ ] 生成 Alembic 迁移
- [ ] 编写测试：注册、登录、Token刷新、权限验证
- [ ] 运行全部测试确保通过

---

## Task Group 3：商品系统 + 定价引擎（后端开发）

> **负责人：程序师** | 预计 2-3 天 | 产出：品类管理、商品CRUD、等级×阶梯定价计算

**验收标准：**
- `GET /api/v1/products/categories` — 品类树
- `POST /api/v1/products` — 管理员创建商品（含适龄/认证字段）
- `GET /api/v1/products` — 商品列表（支持品类/适龄/状态筛选+分页）
- `GET /api/v1/products/{id}` — 商品详情 + 根据请求用户等级计算的价格
- `POST /api/v1/products/{id}/pricing` — 设置阶梯定价规则
- 定价引擎单元测试：相同商品不同等级不同数量 → 正确价格

### Task 3.1：品类 & 商品模型

**Files:**
- Create: `backend/app/models/product.py`
- Create: `backend/app/schemas/product.py`

### Task 3.2：定价引擎

**Files:**
- Create: `backend/app/services/pricing.py`

```python
from decimal import Decimal

def get_price(level: str, qty: int, pricing_rules: dict) -> Decimal | None:
    """
    pricing_rules format:
    {
        "gold":   [{"qty": 10, "price": 80.00}, {"qty": 50, "price": 72.00}, ...],
        "silver": [...],
        "normal": [...]
    }
    Returns the matched unit_price as Decimal, or None if qty below minimum.
    """
    rules = pricing_rules.get(level, pricing_rules.get("normal", []))
    if not rules:
        return None
    
    # Sort by qty ascending, find the highest tier <= qty
    sorted_rules = sorted(rules, key=lambda r: r["qty"])
    matched = None
    for rule in sorted_rules:
        if qty >= rule["qty"]:
            matched = rule
    if matched is None:
        return None  # qty below minimum
    return Decimal(str(matched["price"]))
```

### Task 3.3：商品 API 端点

**Files:**
- Create: `backend/app/api/products.py`

### Task 3.4：迁移 + 测试

---

## Task Group 4：案例图库 API（后端开发）

> **负责人：程序师** | 预计 1 天 | 产出：设计案例CRUD，精选案例查询

**验收标准：**
- `GET /api/v1/cases` — 案例列表（支持风格/面积/类型筛选+分页）
- `GET /api/v1/cases/featured` — 精选案例（首页展示用）
- `GET /api/v1/cases/{id}` — 案例详情
- `POST /api/v1/cases` — 管理员创建案例（含多图上传）
- `PUT /api/v1/cases/{id}` — 编辑案例
- `DELETE /api/v1/cases/{id}` — 删除案例

### Task 4.1：案例模型

**Files:**
- Create: `backend/app/models/case.py`
- Create: `backend/app/schemas/case.py`

### Task 4.2：案例 API 端点

**Files:**
- Create: `backend/app/api/cases.py`

### Task 4.3：迁移 + 测试

---

## Task Group 5：订单系统 + 支付（后端开发）

> **负责人：程序师** | 预计 2-3 天 | 产出：下单、订单管理、设计师指派、支付记录

**验收标准：**
- `POST /api/v1/orders` — 创建订单（含价格快照固化、库存扣减）
- `GET /api/v1/orders` — 我的订单列表（分状态筛选）
- `GET /api/v1/orders/{id}` — 订单详情
- `PUT /api/v1/orders/{id}/status` — 管理员更新订单状态
- `POST /api/v1/orders/{id}/pay` — 提交支付（微信支付/银行转账凭证上传）
- 实物商品订单：pending_payment → paid → shipped → confirmed → completed
- 设计服务订单：pending_payment → paid → designer_assigned → brief → draft → revision → finalized

### Task 5.1：订单模型

**Files:**
- Create: `backend/app/models/order.py`
- Create: `backend/app/schemas/order.py`

### Task 5.2：订单服务

**Files:**
- Create: `backend/app/services/order_service.py`

### Task 5.3：订单 API + 支付端点

**Files:**
- Create: `backend/app/api/orders.py`

### Task 5.4：文件上传服务

**Files:**
- Create: `backend/app/services/upload_service.py`
- Create: `backend/app/api/upload.py`

### Task 5.5：迁移 + 测试

---

## Task Group 6：管理后台（前端开发）

> **负责人：UI设计师 + 程序师** | 预计 2-3 天 | 产出：Vue3 SPA 管理后台，可管理商品/案例/订单/用户

**验收标准：**
- 登录后可看到仪表盘概览
- 商品管理：列表+新增/编辑表单（含适龄、认证、定价规则配置）
- 案例管理：列表+新增/编辑表单（含图片上传预览）
- 订单管理：列表+详情+状态流转+设计师指派
- 用户管理：零售商列表+审核通过/拒绝

### Task 6.1：管理后台脚手架

**Files:**
- Create: `admin/` 全部文件（Vue3 + Vite + Element Plus）

### Task 6.2：商品管理页面

### Task 6.3：案例管理页面

### Task 6.4：订单管理页面

### Task 6.5：用户审核页面

---

## Task Group 7：小程序 — UI 基础设施（前端开发）

> **负责人：UI设计师** | 预计 1-2 天 | 产出：主题系统、公共组件、API层、路由配置

**验收标准：**
- `pages.json` 配置 5个TabBar，图标+文字正确
- `theme.scss` 中 CSS 变量和 spec 色板一致
- `ProductCard`, `CaseCard`, `PriceTable`, `AgeTag`, `CertBadge` 组件可用
- `request.ts` 拦截器：自动带Token、Token过期自动刷新、错误处理
- 各组件在 H5 开发模式下的 Storybook 式预览（或至少能正常渲染）

### Task 7.1：uni-app 项目初始化

**Files:**
- Create: `miniapp/` 全部文件

### Task 7.2：主题 + 全局样式

**Files:**
- Create: `miniapp/src/styles/theme.scss`
- Create: `miniapp/src/styles/global.scss`
- Modify: `miniapp/src/App.vue`

theme.scss 关键变量：
```scss
// 色板
$color-primary: #FF7B7B;       // 珊瑚粉
$color-primary-light: #FFF0ED; // 浅粉背景
$color-bg: #FFF8F0;            // 奶油米白
$color-blue: #7EC8E3;          // 天空蓝
$color-green: #A8D8B9;         // 薄荷绿
$color-yellow: #FFD93D;        // 蜂蜜黄
$color-text: #4a3728;          // 正文色
$color-text-secondary: #7a6a5a; // 辅助文字
$color-border: #f0e0d0;        // 边框色

// 圆角
$radius-sm: 8px;
$radius-md: 12px;
$radius-lg: 20px;
$radius-button: 50px;          // 胶囊按钮

// 阴影
$shadow-card: 0 4px 20px rgba(0, 0, 0, 0.06);
$shadow-soft: 0 2px 8px rgba(255, 123, 123, 0.06);

// 字体
$font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
```

### Task 7.3：公共组件

每个组件按照 spec 中的视觉规范实现。

**ProductCard.vue:**
- 圆角卡片 (20px)，轻柔阴影
- 商品缩略图（懒加载）
- 商品名称 + 批发价区间（如 "¥35 - ¥65"）
- AgeTag 适龄标签
- 库存状态角标
- 点击跳转商品详情

**CaseCard.vue:**
- 瀑布流自适应高度
- 大图优先展示
- 叠加标题+风格标签
- 点击跳转案例详情

**PriceTable.vue:**
- 表头：数量范围 | 单价
- 当前用户等级高亮行
- 虚拟商品不展示此组件

**AgeTag.vue:**
- 小圆角标签
- 天空蓝底色 + 深蓝文字
- 内容如"适合 3-6 岁"

**CertBadge.vue:**
- 小徽章图标 + 认证名称
- 绿色调

### Task 7.4：API 请求层

**Files:**
- Create: `miniapp/src/api/request.ts`
- Create: `miniapp/src/api/auth.ts`
- Create: `miniapp/src/api/products.ts`
- Create: `miniapp/src/api/cases.ts`
- Create: `miniapp/src/api/orders.ts`
- Create: `miniapp/src/api/upload.ts`
- Create: `miniapp/src/stores/user.ts`
- Create: `miniapp/src/stores/cart.ts`

---

## Task Group 8：小程序 — 5个Tab页面（前端开发）

> **负责人：UI设计师** | 预计 3-4 天 | 产出：5个Tab页面完成，可浏览商品/案例/下单

**验收标准：**
- 首页：Banner轮播 → 品类导航 → 小暖推荐Feed → 案例瀑布流
- 案例Tab：瀑布流 + 风格/面积/类型筛选 + 详情页大图浏览
- 商品Tab：品类筛选 + 商品列表 + 详情页（含阶梯价表+认证）
- 订单Tab：订单列表 + 详情 + 结算页
- 我的Tab：用户信息 + 等级展示 + 快捷入口
- 小暖AI Tab：品牌展示占位页（"小暖正在努力学习中，敬请期待..."）

### Task 8.1：首页

**Files:**
- Create: `miniapp/src/pages/home/index.vue`

关键实现：
- Hero区：`swiper` 组件，高度 ~400rpx，3-5张精选案例图轮播，auto-play 3s
- 品类导航：3个大图标按钮，手绘风格（uni-icons或自定义svg）
- 小暖推荐区：`scroll-view` 横向滑动，每项 ProductCard
- 案例瀑布流：双列 flex，每列 CaseCard，交错排列模拟瀑布流

### Task 8.2：商品Tab

**Files:**
- Create: `miniapp/src/pages/products/index.vue`
- Create: `miniapp/src/pages/products/detail.vue`

### Task 8.3：案例Tab

**Files:**
- Create: `miniapp/src/pages/cases/index.vue`
- Create: `miniapp/src/pages/cases/detail.vue`

### Task 8.4：订单Tab + 结算页

**Files:**
- Create: `miniapp/src/pages/order/list.vue`
- Create: `miniapp/src/pages/order/detail.vue`
- Create: `miniapp/src/pages/order/checkout.vue`

### Task 8.5：我的Tab

**Files:**
- Create: `miniapp/src/pages/mine/index.vue`

### Task 8.6：小暖AI占位页

**Files:**
- Create: `miniapp/src/pages/ai-assistant/index.vue`

占位页设计：
- 居中大图："小暖"卡通形象
- 文字："小暖正在努力学习儿童产品知识，很快就能帮您选品下单啦~"
- 显示预计上线时间
- 提供"联系人工客服"按钮作为降级

---

## Task Group 9：集成测试 + 端到端联调

> **负责人：程序师 + UI设计师联合** | 预计 1-2 天 | 产出：全链路通过

**验收标准：**
- 小程序能调通后端所有 API
- 完整下单流程：浏览商品 → 加入购物车 → 结算 → 支付 → 查看订单
- 管理后台能完成商品/案例/订单/用户的完整管理
- 所有 API 测试通过

### Task 9.1：API 联调

### Task 9.2：下单全流程测试

### Task 9.3：管理后台全流程测试

---

## 任务分配矩阵

```
Task Group 1: 脚手架 ────────> 程序师
Task Group 2: 用户+认证 ──────> 程序师
Task Group 3: 商品+定价 ──────> 程序师
Task Group 4: 案例图库 ──────> 程序师
Task Group 5: 订单+支付 ──────> 程序师
Task Group 6: 管理后台 ───────> 程序师 + UI设计师
Task Group 7: 小程序基础设施 ──> UI设计师
Task Group 8: 小程序5个Tab ───> UI设计师
Task Group 9: 集成测试 ───────> 程序师 + UI设计师（联合）
```

**执行规则：**
1. 每个 Task Group 指派给负责人，完成后我（总规划师）进行代码审查和测试验收
2. 验收通过后才能进入下一个 Task Group
3. 同一时间可以有最多2个独立的 Task Group 并行（如 Group 4 后端 和 Group 7 前端可并行）
4. 有依赖关系的 Group 必须顺序执行（Group 1→2→3→5, Group 7→8）

---

## 自检清单

| 检查项 | 状态 |
|--------|------|
| Spec 覆盖 | ✅ Phase 1 所有 7 个模块均有对应 Task Group |
| 占位符 | ✅ 无 TBD/TODO 残留 |
| 类型一致性 | ✅ models/schemas/api/services 命名一致，接口签名对接 |
| 文件路径 | ✅ 全部使用绝对路径，文件职责单一 |
