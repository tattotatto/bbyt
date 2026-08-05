#!/usr/bin/env python3
"""Fix port conflicts, restart with new code, verify admin"""
import paramiko, time

SSH = paramiko.SSHClient()
SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
SSH.connect("192.168.50.157", username="johnwoo", password="REDACTED", timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = SSH.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out.strip(), err.strip()

# Fix docker-compose.yml to use "expose" instead of "ports" for db/redis
# This avoids port conflicts with hxbaby (6379, 5432)
print("[1] Fixing docker-compose.yml (remove external db/redis ports)...")
NEW_COMPOSE = """services:
  api:
    build: .
    ports:
      - "7000:7000"
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
    expose:
      - "5432"
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
    expose:
      - "6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
"""

# Write compose file via SFTP
sftp = SSH.open_sftp()
with sftp.file("/opt/hxmall/docker-compose.yml", "w") as f:
    f.write(NEW_COMPOSE)
print("  OK - docker-compose.yml updated")

# Upload admin dist tarball
import os
local_tar = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hxmall-admin.tar.gz")
if os.path.exists(local_tar):
    print("[1.5] Uploading new admin build...")
    sftp.put(local_tar, "/tmp/hxmall-admin-v2.tar.gz")
    print("  Uploaded")
    # Extract
    code, out, err = run("rm -rf /opt/hxmall/admin-dist && mkdir -p /opt/hxmall/admin-dist && tar -xzf /tmp/hxmall-admin-v2.tar.gz -C /opt/hxmall/admin-dist/ && ls /opt/hxmall/admin-dist/")
    print(f"  Extracted: {out}")
    # Copy into container
    code, out, err = run("docker cp /opt/hxmall/admin-dist/. hxmall-api-1:/app/admin-dist/ 2>&1")
    print(f"  Copied to container: {out} {err}")

# Stop old containers
print("[2] Stopping old hxmall-backend containers...")
code, out, err = run("docker stop hxmall-backend-api-1 hxmall-backend-db-1 hxmall-backend-redis-1 2>/dev/null; echo done")
print(f"  {out}")
code, out, err = run("docker rm hxmall-backend-api-1 hxmall-backend-db-1 hxmall-backend-redis-1 2>/dev/null; echo done")
print(f"  removed old containers")

code, out, err = run("docker stop hxmall-api 2>/dev/null; docker rm hxmall-api 2>/dev/null; echo done")
print(f"  cleaned up standalone")

# Start new compose
print("[3] Starting hxmall with updated code (admin support)...")
code, out, err = run("cd /opt/hxmall && docker compose up -d 2>&1", timeout=120)
print(f"  {out}")
if err:
    print(f"  ERR: {err}")

time.sleep(5)

# Check compose status
print("[4] Container status:")
code, out, err = run("cd /opt/hxmall && docker compose ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'")
print(f"  {out}")

# Verify
print("\n[5] Verification:")
time.sleep(3)

checks = [
    ("curl -s http://localhost:7000/api/v1/health", "API health"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:7000/admin/", "Admin page HTTP code"),
    ("curl -s http://localhost:7000/admin/ 2>/dev/null | head -1", "Admin page content"),
]

for cmd, desc in checks:
    code, out, err = run(cmd)
    print(f"  [{desc}] code={code}, output={out[:120]}")
    if err and "ERR" not in desc:
        print(f"    stderr: {err[:200]}")

sftp.close()
SSH.close()

print("\nDone! Admin should be at: http://192.168.50.157:7000/admin/")
