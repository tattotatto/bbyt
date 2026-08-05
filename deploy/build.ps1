# ============================================================
# HX Mall 一键构建部署脚本
# 1. 构建管理后台 (admin/dist)
# 2. 拷贝到 backend/admin-dist
# 3. 构建 Docker 镜像
# 4. 推送到服务器
#
# 用法：.\deploy\build.ps1 -Server root@your-server-ip
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Server,                     # SSH 目标

    [string]$ContainerName = "hxmall-api",
    [string]$RemoteDir = "/opt/hxmall"
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HX Mall 一键构建部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================
# 1. 构建管理后台
# ============================
Write-Host "[1/5] 构建管理后台..." -ForegroundColor Green
if (Test-Path "admin\dist") {
    Remove-Item -Recurse -Force "admin\dist"
}
Push-Location admin
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "管理后台构建失败"
    }
    Write-Host "  管理后台构建完成 ($((Get-ChildItem -Recurse admin\dist | Measure-Object -Property Length -Sum).Sum / 1KB) KB)" -ForegroundColor Gray
} finally {
    Pop-Location
}

# ============================
# 2. 拷贝到 backend/admin-dist
# ============================
Write-Host "[2/5] 拷贝管理后台到 backend/admin-dist..." -ForegroundColor Green
$adminDistDir = "backend\admin-dist"
if (Test-Path $adminDistDir) {
    Remove-Item -Recurse -Force $adminDistDir
}
Copy-Item -Recurse "admin\dist" $adminDistDir
Write-Host "  已拷贝到 $adminDistDir" -ForegroundColor Gray

# ============================
# 3. 构建 Docker 镜像
# ============================
Write-Host "[3/5] 构建 Docker 镜像..." -ForegroundColor Green
Push-Location backend
docker build -t $ContainerName:latest .
if ($LASTEXITCODE -ne 0) {
    throw "Docker 构建失败"
}
Pop-Location
Write-Host "  镜像构建完成: ${ContainerName}:latest" -ForegroundColor Gray

# ============================
# 4. 导出并上传到服务器
# ============================
Write-Host "[4/5] 上传镜像到服务器..." -ForegroundColor Green
$imageFile = "hxmall-api-latest.tar"
docker save ${ContainerName}:latest -o $imageFile
scp $imageFile "${Server}:/tmp/"
ssh $Server "docker load -i /tmp/$imageFile && rm /tmp/$imageFile"
Remove-Item $imageFile
Write-Host "  镜像已上传" -ForegroundColor Gray

# ============================
# 5. 重启服务
# ============================
Write-Host "[5/5] 重启服务..." -ForegroundColor Green

# 上传 docker-compose.yml
scp "backend\docker-compose.yml" "${Server}:$RemoteDir/docker-compose.yml"

ssh $Server @"
cd $RemoteDir
docker-compose down
docker-compose up -d
sleep 3
docker-compose ps
"@

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API 健康检查:  http://服务器IP:7000/api/v1/health"
Write-Host "  管理后台:     http://服务器IP:7000/admin"
Write-Host "  默认登录页:     http://服务器IP:7000/admin/login"
Write-Host ""
Write-Host "  如果通过现有 nginx 代理访问："
Write-Host "  管理后台:     http://服务器IP/admin  (需 nginx 配置)"
Write-Host ""
