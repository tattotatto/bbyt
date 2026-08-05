FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 管理后台静态文件（由 build.ps1/build.sh 在构建前拷贝到 backend/admin-dist）
# 如果不存在则创建空目录避免 COPY 失败
COPY admin-dist ./admin-dist

EXPOSE 7000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
