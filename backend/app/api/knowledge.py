"""知识库管理 API"""
import os
from pathlib import Path
import aiofiles
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.knowledge import KnowledgeEntry
from app.ai.knowledge.sync import sync_all_products
from app.ai.knowledge.parser import parse_document
from app.ai.knowledge.embedder import embed_text
from app.schemas.knowledge import KnowledgeEntryCreate
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.deps import require_role

router = APIRouter()


@router.get(
    "/entries",
    response_model=APIResponse[PaginatedResponse[dict]],
    summary="知识条目列表",
)
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeEntry)
    count_query = select(func.count()).select_from(KnowledgeEntry)
    if source_type:
        query = query.where(KnowledgeEntry.source_type == source_type)
        count_query = count_query.where(KnowledgeEntry.source_type == source_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(KnowledgeEntry.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    entries = result.scalars().all()

    items = [
        {
            "id": str(e.id),
            "title": e.title,
            "source_type": e.source_type,
            "weight": e.weight,
            "status": e.status,
        }
        for e in entries
    ]
    return APIResponse.ok(
        data=PaginatedResponse(
            items=items, total=total, page=page, page_size=page_size
        )
    )


@router.post(
    "/entries",
    response_model=APIResponse[dict],
    summary="手动录入知识条目（管理员/运营）",
)
async def create_entry(
    req: KnowledgeEntryCreate,
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    entry = KnowledgeEntry(
        title=req.title, content=req.content, source_type=req.source_type
    )
    db.add(entry)
    await db.flush()
    return APIResponse.ok(
        data={"id": str(entry.id), "title": entry.title}, message="知识条目创建成功"
    )


@router.post(
    "/sync",
    response_model=APIResponse[dict],
    summary="全量同步商品到知识库（管理员/运营）",
)
async def trigger_sync(
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    count = await sync_all_products(db)
    return APIResponse.ok(
        data={"synced_count": count}, message=f"已同步 {count} 个商品"
    )


@router.post("/upload", response_model=APIResponse[dict], summary="上传文档到知识库（管理员）")
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form(default="manual"),
    _admin: dict = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF/Word/Excel/TXT 文档，自动解析并存储到知识库"""
    # 1. 保存临时文件
    upload_dir = Path("./uploads/knowledge")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / file.filename
    content_bytes = await file.read()
    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(content_bytes)

    # 2. 判断文件类型
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    file_type_map = {"pdf": "pdf", "doc": "word", "docx": "word", "xls": "excel", "xlsx": "excel", "txt": "txt"}
    file_type = file_type_map.get(ext, "txt")

    # 3. 解析文本
    text = await parse_document(str(temp_path), file_type)
    if not text or text.startswith("PDF 解析失败") or text.startswith("Word 解析失败"):
        # 清理临时文件
        os.remove(str(temp_path))
        raise HTTPException(status_code=400, detail=text or "文档解析无内容")

    # 4. 分段 + Embedding + 存储（简单按段落分段）
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 10]
    if not paragraphs:
        paragraphs = [text[:500]]  # 至少一段

    entries = []
    for para in paragraphs[:20]:  # 最多20段
        try:
            embedding = await embed_text(para)
        except Exception:
            embedding = None  # 没有 Embedding API 时跳过

        entry = KnowledgeEntry(
            source_type=source_type,
            title=f"{file.filename} - {para[:50]}",
            content=para,
            embedding=embedding,
        )
        db.add(entry)
        entries.append(entry)

    # 5. 清理
    os.remove(str(temp_path))
    await db.flush()

    return APIResponse.ok(
        data={"filename": file.filename, "paragraphs": len(entries)},
        message=f"文档解析完成，已录入 {len(entries)} 条知识"
    )
