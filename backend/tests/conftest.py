"""测试 fixtures：用 SQLite 内存数据库，不依赖外部 PostgreSQL"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# 内存数据库 — 每个连接看到同一个数据库
TEST_DATABASE_URL = "sqlite+aiosqlite://"

from app.main import app
from app.models import Base

# 模块级引擎（所有测试共享）
_test_engine = None
_test_session_factory = None


def get_test_engine():
    global _test_engine
    if _test_engine is None:
        _test_engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return _test_engine


def get_test_session_factory():
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = async_sessionmaker(
            get_test_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _test_session_factory


@pytest_asyncio.fixture(scope="function")
async def client():
    """每个测试函数获得独立的表结构（create + drop）"""
    global _test_engine, _test_session_factory

    # 创建引擎（首次）并建表
    engine = get_test_engine()
    _test_session_factory = get_test_session_factory()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 覆盖 FastAPI 的 get_db 依赖
    async def override_get_db():
        async with _test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides = {}
    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    # 让测试辅助函数也能用测试数据库
    import sys
    sys.modules["app.database"].async_session_factory = _test_session_factory

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as ac:
        yield ac

    # 清理：删表（不销毁引擎，复用）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """测试辅助 fixture：直接访问数据库（用于手动审批用户等操作）"""
    factory = get_test_session_factory()
    async with factory() as session:
        yield session

