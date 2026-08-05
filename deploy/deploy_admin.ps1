# ============================================================
# HX Mall 管理后台部署脚本 (PowerShell)
# 将 admin/dist 上传到服务器并配置 nginx
#
# 用法：.\deploy\deploy_admin.ps1 -Server root@your-server-ip
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Server,                     # SSH 目标，例如 root@192.168.1.100

    [string]$RemoteDir = "/opt/hxmall-admin",  # 服务器上的部署目录
    [string]$LocalDist = ".\admin\dist"        # 本地构建产物路径
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

Write-Host "===== HX Mall 管理后台部署 =====" -ForegroundColor Cyan
Write-Host "目标服务器: $Server" -ForegroundColor Yellow
Write-Host "本地构建: $LocalDist" -ForegroundColor Yellow
Write-Host "远程路径: $RemoteDir" -ForegroundColor Yellow
Write-Host ""

# 1. 验证本地 dist 存在
if (-not (Test-Path $LocalDist)) {
    Write-Host "[错误] 未找到构建产物: $LocalDist" -ForegroundColor Red
    Write-Host "请先运行: cd admin && npm run build" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] 检查构建产物..." -ForegroundColor Green
$distSize = (Get-ChildItem -Recurse $LocalDist | Measure-Object -Property Length -Sum).Sum
Write-Host "  dist 大小: $([math]::Round($distSize / 1MB, 2)) MB" -ForegroundColor Gray

# 2. 在服务器上创建目录
Write-Host "[2/4] 在服务器上创建部署目录..." -ForegroundColor Green
ssh $Server "mkdir -p $RemoteDir/dist"

# 3. 上传 dist 文件（使用 scp -r 递归上传）
Write-Host "[3/4] 上传管理后台文件..." -ForegroundColor Green
scp -r "$LocalDist\*" "${Server}:$RemoteDir/dist/"

Write-Host "  文件上传完成" -ForegroundColor Gray

# 4. 配置说明
Write-Host "[4/4] 配置 Nginx..." -ForegroundColor Green

# 上传新的 nginx 配置文件
if (Test-Path ".\deploy\nginx-hxmall.conf") {
    scp ".\deploy\nginx-hxmall.conf" "${Server}:/tmp/nginx-hxmall.conf"
    Write-Host "  nginx 配置文件已上传到 /tmp/nginx-hxmall.conf" -ForegroundColor Gray
}

# 输出后续手动操作说明
Write-Host ""
Write-Host "===== 上传完成！请在服务器上执行以下操作 =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 将 nginx 配置拷贝到位："
Write-Host "   cp /tmp/nginx-hxmall.conf /opt/hxbaby/nginx.conf   # 如果共用 hxbaby"
Write-Host "   # 或者加入现有 nginx 的 conf.d 目录"
Write-Host ""
Write-Host "2. 验证 nginx 配置语法："
Write-Host "   docker run --rm -v /opt/hxbaby/nginx.conf:/tmp/nginx.conf:ro nginx:alpine nginx -t -c /tmp/nginx.conf"
Write-Host ""
Write-Host "3. 重载 nginx："
Write-Host "   docker restart hxbaby-nginx   # 或 docker exec nginx-container nginx -s reload"
Write-Host ""
Write-Host "4. 访问管理后台："
Write-Host "   http://<服务器IP>/admin    （共用路径方案）"
Write-Host "   http://admin.<域名>/       （独立子域名方案）"
Write-Host ""
Write-Host "5. 通过管理后台登录（需先在数据库创建管理员账号）" -ForegroundColor Yellow
Write-Host "   默认登录页: http://<服务器IP>/admin/login"
Write-Host ""
Write-Host "===== 管理后台功能 =====" -ForegroundColor Cyan
Write-Host "  📊 仪表盘    — 商品/订单/用户/案例统计概览"
Write-Host "  📦 商品管理   — 新增/编辑/上下架 + 阶梯定价配置"
Write-Host "  🎨 案例管理   — 设计案例图库 CRUD"
Write-Host "  📋 订单管理   — 订单状态流转 + 设计师指派"
Write-Host "  👥 用户管理   — 零售商审核（通过/拒绝）+ 等级/额度设定"
