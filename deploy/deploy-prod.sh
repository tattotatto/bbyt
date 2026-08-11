#!/usr/bin/env bash
# ============================================================
# HX Mall 生产一键部署脚本
#
# 用法:
#   ./deploy/deploy-prod.sh <SERVER> [SSH_USER] [REMOTE_DIR]
#   例: ./deploy/deploy-prod.sh 1.2.3.4 deployer /opt/hxmall
#
# 前置:
#   - 本机已配置 SSH 密钥登录目标服务器（无需密码）
#   - 服务器已装 Docker + Docker Compose v2
#   - 已按 deploy/.env.example 准备好 deploy/.env.production
#
# 流程: 构建 admin → 构建镜像 → 推镜像 → 上传配置 → up -d
#        → 迁移 → 建管理员 → 验证
# ============================================================
set -euo pipefail

# ---------- 参数 ----------
SERVER="${1:?用法: $0 <SERVER> [SSH_USER] [REMOTE_DIR]}"
SSH_USER="${2:-root}"
REMOTE_DIR="${3:-/opt/hxmall}"
IMAGE="hxmall-api:latest"
TARBALL="/tmp/hxmall-api-image.tar"

# ---------- 路径 ----------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADMIN_DIR="$REPO_ROOT/admin"
BACKEND_DIR="$REPO_ROOT/backend"
ENV_PROD="$SCRIPT_DIR/.env.production"

SSH_CMD="ssh ${SSH_USER}@${SERVER}"
SCP_CMD="scp"

step() { echo ""; echo "==> [$1/8] $2"; }

# ---------- 0. 预检 ----------
echo "==> [0/8] 预检"
$SSH_CMD "docker --version && docker compose version" >/dev/null 2>&1 \
  || { echo "[!] 无法 SSH 或服务器缺 Docker，请检查"; exit 1; }
[ -f "$ENV_PROD" ] || echo "[!] 未找到 $ENV_PROD —— 将跳过 .env 上传（JWT/WECHAT 用默认/空值，正式上线前务必补齐）"

# ---------- 1. 构建管理后台 ----------
step 1 "构建管理后台"
( cd "$ADMIN_DIR" && npm install && npm run build )
rm -rf "$BACKEND_DIR/admin-dist"
mkdir -p "$BACKEND_DIR/admin-dist"
cp -r "$ADMIN_DIR/dist/." "$BACKEND_DIR/admin-dist/"
echo "   admin-dist 已更新"

# ---------- 2. 构建后端镜像 ----------
step 2 "构建后端镜像 $IMAGE"
docker build -t "$IMAGE" "$BACKEND_DIR"

# ---------- 3. 导出并推送镜像 ----------
step 3 "导出并上传镜像"
docker save "$IMAGE" -o "$TARBALL"
$SCP_CMD "$TARBALL" "${SSH_USER}@${SERVER}:/tmp/"
$SSH_CMD "docker load -i /tmp/$(basename "$TARBALL") && rm -f /tmp/$(basename "$TARBALL")"
rm -f "$TARBALL"

# ---------- 4. 上传 compose 与 .env ----------
step 4 "上传 docker-compose.yml 与 .env"
$SSH_CMD "mkdir -p $REMOTE_DIR/uploads"
$SCP_CMD "$BACKEND_DIR/docker-compose.yml" "${SSH_USER}@${SERVER}:$REMOTE_DIR/"
if [ -f "$ENV_PROD" ]; then
  # 备份服务器已有 .env（首次部署时无此文件）
  $SSH_CMD "[ -f $REMOTE_DIR/.env ] && cp $REMOTE_DIR/.env $REMOTE_DIR/.env.bak.\$(date +%Y%m%d%H%M%S) || true"
  $SCP_CMD "$ENV_PROD" "${SSH_USER}@${SERVER}:$REMOTE_DIR/.env"
  echo "   .env.production -> $REMOTE_DIR/.env（旧 .env 已备份）"
fi

# ---------- 5. 启动服务 ----------
step 5 "docker compose up -d"
$SSH_CMD "cd $REMOTE_DIR && docker compose up -d"
sleep 8

# ---------- 6. 数据库迁移 ----------
step 6 "数据库迁移（alembic upgrade head）"
$SSH_CMD "cd $REMOTE_DIR && docker compose exec -T api alembic upgrade head"

# ---------- 7. 初始化管理员 ----------
step 7 "初始化管理员（不存在则创建 13800000000/admin123）"
$SSH_CMD "cd $REMOTE_DIR && docker compose exec -T api python -" <<'PY'
import asyncio
from app.database import async_session_factory
from app.models.user import User, UserRole, UserStatus, RetailerLevel
from app.services.auth_service import hash_password
from sqlalchemy import select
async def main():
    async with async_session_factory() as s:
        r = await s.execute(select(User).where(User.role == UserRole.ADMIN))
        if r.scalars().first():
            print("admin exists")
        else:
            s.add(User(phone="13800000000", hashed_password=hash_password("admin123"),
                       role=UserRole.ADMIN, level=RetailerLevel.NORMAL, status=UserStatus.ACTIVE))
            await s.commit()
            print("admin created (13800000000 / admin123) - 请立即改密")
asyncio.run(main())
PY

# ---------- 8. 验证 ----------
step 8 "验证"
sleep 3
$SSH_CMD "curl -s http://localhost:7000/api/v1/health; echo; curl -s -o /dev/null -w 'admin http %{http_code}\n' http://localhost:7000/admin/"

echo ""
echo "===================================================="
echo "  部署完成！"
echo "  API:    https://baby.mx.yn.cn/api/v1/health"
echo "  管理台: https://baby.mx.yn.cn/admin/"
echo "  小程序: 开发者工具上传发布 + 配置合法域名"
echo "===================================================="
