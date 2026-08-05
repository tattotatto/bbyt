"""文件上传 API 端点"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.api.deps import require_role
from app.schemas.common import APIResponse
from app.services.upload_service import upload_image
from app.services.upload_service import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_SIZE

router = APIRouter()


@router.post("/image", response_model=APIResponse[dict], summary="上传图片")
async def upload_single_image(
    file: UploadFile = File(..., description="图片文件（JPG/PNG/WebP/GIF/BMP，最大10MB）"),
    _admin: dict = Depends(require_role("admin", "operator")),
):
    """
    上传单张图片，自动转换为 WebP 格式并生成缩略图。

    - **file**: 上传的图片文件
    - 返回: `{"url": "...", "thumb_url": "...", "filename": "...", "size": ...}`
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未选择文件")

    try:
        result = await upload_image(file)
        return APIResponse.ok(data=result, message="上传成功")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件处理失败: {str(e)}")


@router.post("/images", response_model=APIResponse[list[dict]], summary="批量上传图片")
async def upload_multiple_images(
    files: list[UploadFile] = File(..., description="图片文件列表（最多9张）"),
    _admin: dict = Depends(require_role("admin", "operator")),
):
    """
    批量上传图片，每张自动转换为 WebP 并生成缩略图。

    - **files**: 图片文件列表（最多9张）
    - 返回: `[{url, thumb_url, filename, size}, ...]`
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未选择文件")

    if len(files) > 9:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单次最多上传9张图片")

    results = []
    errors = []
    for file in files:
        try:
            result = await upload_image(file)
            results.append(result)
        except ValueError as e:
            errors.append({"filename": file.filename, "error": str(e)})
        except Exception as e:
            errors.append({"filename": file.filename, "error": f"处理失败: {str(e)}"})

    if errors and not results:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"全部上传失败: {errors}")

    return APIResponse.ok(
        data=results,
        message=f"上传完成: 成功 {len(results)} 张" + (f"，失败 {len(errors)} 张" if errors else ""),
    )
