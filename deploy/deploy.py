#!/usr/bin/env python3
"""
HX Mall deployment script - upload admin + update backend + rebuild
"""
import paramiko, os, sys, time

SERVER = os.environ.get("HXMALL_SERVER", "192.168.50.157")
USER = os.environ.get("HXMALL_SERVER_USER", "johnwoo")
# 密码不再写死在代码里：从环境变量读取，或改用 SSH 密钥
PASSWORD = os.environ.get("HXMALL_SERVER_PASSWORD", "")
if not PASSWORD:
    raise SystemExit("请设置环境变量 HXMALL_SERVER_PASSWORD（或用 SSH 密钥代替密码）")
PROJECT_ROOT = "/opt/hxmall"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

print("=" * 60)
print("HX Mall Deploy")
print("=" * 60)

# Connect
print("\n[1/6] Connecting to server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=15)
sftp = ssh.open_sftp()
print("  OK")

def run(cmd, timeout=60):
    """Execute command and return stdout, stderr"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    return exit_code, out, err

# Upload admin tarball
print("\n[2/6] Uploading admin dist tarball...")
tarball_path = os.path.join(SCRIPT_DIR, "hxmall-admin.tar.gz")
sftp.put(tarball_path, "/opt/hxmall/admin-dist.tar.gz")
size = sftp.stat("/opt/hxmall/admin-dist.tar.gz").st_size
print(f"  Uploaded: {size:,} bytes")

# Extract admin-dist
print("\n[3/6] Extracting admin-dist...")
code, out, err = run("cd /opt/hxmall && rm -rf admin-dist && mkdir -p admin-dist && tar -xzf admin-dist.tar.gz -C admin-dist/ && ls admin-dist/")
print(f"  {out.strip()}")
if err:
    print(f"  ERR: {err.strip()}")

# Upload updated main.py
print("\n[4/6] Uploading updated main.py...")
local_main = os.path.join(PROJECT_DIR, "backend", "app", "main.py")
if os.path.isfile(local_main):
    sftp.put(local_main, "/opt/hxmall/app/main.py")
    print("  OK - main.py updated (with /admin route)")
else:
    print(f"  WARN: {local_main} not found")

# Upload updated Dockerfile
local_dockerfile = os.path.join(PROJECT_DIR, "backend", "Dockerfile")
if os.path.isfile(local_dockerfile):
    sftp.put(local_dockerfile, "/opt/hxmall/Dockerfile")
    print("  OK - Dockerfile updated")

# Fix docker-compose.yml port to match Dockerfile (7000)
print("\n[5/6] Updating docker-compose.yml...")
code, out, err = run("cat /opt/hxmall/docker-compose.yml")
if "7000:7000" in out:
    print("  Port already 7000, OK")
else:
    # Replace 5000:5000 with 7000:7000
    code2, out2, err2 = run("sed -i 's/\"5000:5000\"/\"7000:7000\"/' /opt/hxmall/docker-compose.yml && grep -n port /opt/hxmall/docker-compose.yml")
    print(f"  Updated: {out2.strip()}")

# Rebuild and restart
print("\n[6/6] Rebuilding and restarting...")
cmds = [
    "cd /opt/hxmall && docker compose build api 2>&1",
    "cd /opt/hxmall && docker compose up -d api 2>&1",
]
for cmd in cmds:
    print(f"  >>> {cmd[:60]}...")
    code, out, err = run(cmd, timeout=180)
    # Print last few lines
    lines = (out + err).strip().split('\n')
    for line in lines[-5:]:
        if line.strip():
            print(f"      {line.strip()}")
    if code != 0:
        print(f"  WARN: exit code {code}")

time.sleep(3)

# Verify
print("\n" + "=" * 60)
print("Verification")
print("=" * 60)

checks = [
    ("curl -s http://localhost:7000/api/v1/health", "API health"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:7000/admin/", "Admin page (port 7000)"),
    ("docker ps --filter name=hxmall --format '{{.Names}} {{.Status}}'", "Container status"),
]

for cmd, desc in checks:
    code, out, err = run(cmd, timeout=10)
    status = "OK" if code == 0 and out.strip() else "FAIL"
    print(f"  [{status}] {desc}: {out.strip()[:100]}")
    if err and 'ERR' not in err.upper():
        pass  # stderr from docker ps format is normal

sftp.close()
ssh.close()

print("\n" + "=" * 60)
print("DEPLOY COMPLETE")
print("=" * 60)
print("""
  Admin panel: http://192.168.50.157:7000/admin/
  API health:  http://192.168.50.157:7000/api/v1/health
""")
