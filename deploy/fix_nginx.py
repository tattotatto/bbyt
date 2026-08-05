#!/usr/bin/env python3
"""Fix nginx config - add hxmall API routes + admin SPA to hxbaby nginx"""
import subprocess, time, os

os.chdir('/opt/hxbaby')

# Restore original
subprocess.run(['git', 'checkout', 'nginx.conf'])
subprocess.run(['docker', 'restart', 'hxbaby-nginx'])
time.sleep(3)

# Read original
with open('nginx.conf') as f:
    lines = f.readlines()

# Blocks to insert before 'location /api/'
block = """        # ===== HX Mall 管理后台 SPA =====
        # 静态资源（JS/CSS/图片）
        location /admin/assets/ {
            alias /opt/hxmall-admin/dist/assets/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # 管理后台入口 + SPA 路由回退
        location /admin {
            alias /opt/hxmall-admin/dist;
            try_files $uri $uri/ /admin/index.html;
        }

        # ===== HX Mall API =====
        # WebSocket: AI 对话通道
        location /api/v1/ai/ws/chat {
            proxy_pass http://hxmall-api:7000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 3600s;
        }

        # 后端 API
        location /api/v1/ {
            proxy_pass http://hxmall-api:7000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            client_max_body_size 20m;
        }

"""

# Check if admin SPA files exist
admin_exists = os.path.isdir('/opt/hxmall-admin/dist')
if not admin_exists:
    print("WARNING: /opt/hxmall-admin/dist 不存在 — 管理后台无法访问")
    print("请执行: mkdir -p /opt/hxmall-admin && scp -r admin/dist/* server:/opt/hxmall-admin/dist/")

# Insert before location /api/
result = []
for line in lines:
    if line.strip() == 'location /api/ {' and 'v1' not in line:
        result.append(block)
    result.append(line)

with open('nginx.conf', 'w') as f:
    f.writelines(result)

print('Config updated. Lines:', len(result))

# Verify syntax
r = subprocess.run(
    ['docker', 'run', '--rm', '-v', '/opt/hxbaby/nginx.conf:/tmp/nginx.conf:ro',
     'nginx:alpine', 'nginx', '-t', '-c', '/tmp/nginx.conf'],
    capture_output=True, text=True
)
print('Syntax check:', r.stdout.strip(), r.stderr.strip())

# Restart and test
subprocess.run(['docker', 'restart', 'hxbaby-nginx'])
time.sleep(3)

import urllib.request

# Test API
try:
    resp = urllib.request.urlopen('http://localhost:80/api/v1/health', timeout=5)
    print('HXMall API OK:', resp.read().decode()[:200])
except Exception as e:
    print('HXMall API FAIL:', e)

# Test Admin SPA
try:
    resp = urllib.request.urlopen('http://localhost:80/admin/', timeout=5)
    html = resp.read().decode()
    if 'HX Mall' in html or '管理后台' in html or 'app' in html.lower():
        print('HXMall Admin OK: index.html served')
    else:
        print('HXMall Admin WARN: response but might not be admin:', html[:100])
except Exception as e:
    print('HXMall Admin FAIL:', e)

# Test original
try:
    resp = urllib.request.urlopen('http://localhost:80/health', timeout=5)
    print('Original OK:', resp.read().decode()[:80])
except Exception as e:
    print('Original FAIL:', e)
