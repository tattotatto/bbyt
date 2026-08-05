"""文件上传服务：本地存储 / OSS 上传、WebP 转换、缩略图生成"""
import uuid
import os
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
from PIL import Image
from app.config import get_settings

settings = get_settings()

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"
}
MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # MB → bytes
THUMBNAIL_SIZE = (400, 400)  # 缩略图尺寸


async def validate_image(file: UploadFile) -> None:
    """校验文件类型和大小，不合法时抛出 ValueError"""
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"不支持的文件类型: {file.content_type}，仅支持 JPG/PNG/WebP/GIF/BMP")

    # 读取前几个字节检查实际内容
    contents = await file.read()
    file.size = len(contents)
    await file.seek(0)  # reset

    if len(contents) > MAX_UPLOAD_SIZE:
        raise ValueError(f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)")


async def to_webp(image_bytes: bytes, quality: int = 85) -> bytes:
    """将图片转换为 WebP 格式"""
    img = Image.open(BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    output = BytesIO()
    img.save(output, format="WEBP", quality=quality)
    return output.getvalue()


async def generate_thumbnail(image_bytes: bytes, size: tuple = THUMBNAIL_SIZE) -> bytes:
    """生成缩略图（WebP 格式，正方形裁剪+缩放）"""
    img = Image.open(BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 正方形裁剪（取中心区域）
    w, h = img.size
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    img = img.crop((left, top, left + min_side, top + min_side))

    # 缩放到目标尺寸
    img.thumbnail(size, Image.LANCZOS)

    output = BytesIO()
    img.save(output, format="WEBP", quality=80)
    return output.getvalue()


async def save_file(upload_dir: str, filename: str, file_bytes: bytes) -> str:
    """保存文件到本地磁盘，返回文件的访问 URL 路径"""
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    # 异步写文件
    import aiofiles
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(file_bytes)

    return filepath


async def upload_image(file: UploadFile) -> dict:
    """
    处理单张图片上传的完整流程：
    1. 校验文件
    2. 转换为 WebP
    3. 生成缩略图
    4. 保存原图 + 缩略图
    5. 返回文件 URL

    Returns:
        {"url": str, "thumb_url": str, "filename": str, "size": int}
    """
    await validate_image(file)

    contents = await file.read()
    original_size = len(contents)

    # WebP 转换
    webp_bytes = await to_webp(contents)
    thumb_bytes = await generate_thumbnail(contents)

    # 生成文件名
    unique_name = f"{uuid.uuid4().hex}.webp"
    thumb_name = f"{uuid.uuid4().hex}_thumb.webp"

    # 保存文件
    upload_dir = settings.UPLOAD_DIR or "./uploads"
    img_dir = os.path.join(upload_dir, "images")
    await save_file(img_dir, unique_name, webp_bytes)
    await save_file(img_dir, thumb_name, thumb_bytes)

    # 构建返回 URL（相对路径，实际部署时由 Nginx 或 CDN 映射）
    base_url = "/static/images"
    return {
        "url": f"{base_url}/{unique_name}",
        "thumb_url": f"{base_url}/{thumb_name}",
        "filename": unique_name,
        "size": len(webp_bytes),
        "original_size": original_size,
    }
