from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from app.config import get_settings
from app.database import engine, async_session_factory
from app import redis as redis_module
from app.api import api_router
from app.middleware.exception_handler import global_exception_handler, validation_exception_handler
from app.schemas.common import APIResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_module.init_redis()
    yield
    # Shutdown
    await redis_module.close_redis()
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

# Static files (uploaded images)
uploads_dir = os.path.join(settings.UPLOAD_DIR or "./uploads", "images")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=uploads_dir), name="static_images")

# ===== 管理后台 SPA =====
# 构建产物目录：backend/admin-dist
# 部署时在服务器上执行: npm run build，将 dist 拷贝到 backend/admin-dist
ADMIN_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "admin-dist")

if os.path.isdir(ADMIN_DIST_DIR):
    # 挂载 admin 静态资源（JS/CSS/图片等）
    admin_assets_dir = os.path.join(ADMIN_DIST_DIR, "assets")
    if os.path.isdir(admin_assets_dir):
        app.mount("/admin/assets", StaticFiles(directory=admin_assets_dir), name="admin_assets")

    @app.get("/admin")
    @app.get("/admin/{full_path:path}")
    async def serve_admin_spa(full_path: str = ""):
        """管理后台 SPA — Vue Router history 模式回退"""
        file_path = os.path.join(ADMIN_DIST_DIR, full_path) if full_path else None
        # 如果请求的是实际存在的文件，直接返回
        if file_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # 否则回退到 index.html（Vue Router 处理路由）
        index_path = os.path.join(ADMIN_DIST_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return APIResponse.error(message="管理后台文件未找到，请检查 admin-dist 目录")


@app.get("/api/v1/health", tags=["系统"])
async def health_check():
    db_ok = False
    redis_ok = False
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        db_ok = True
    except Exception:
        pass
    try:
        if redis_module.redis_client is not None:
            await redis_module.redis_client.ping()
            redis_ok = True
    except Exception:
        pass
    return APIResponse.ok(data={"db": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"})
