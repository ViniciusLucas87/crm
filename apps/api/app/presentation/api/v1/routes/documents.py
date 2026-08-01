"""
Company Documents API — upload, list, download, rename, delete.
"""

import os
import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select, delete as sa_delete
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import CompanyDocument
from app.infrastructure.db.session import get_db_session

router = APIRouter()

UPLOAD_DIR = Path("/app/uploads")
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".png", ".jpeg", ".jpg", ".webp", ".zip"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


@router.post("/documents/upload")
async def upload_document(
    company_id: int = Query(),
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Upload a document to a company."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max {MAX_FILE_SIZE // 1024 // 1024}MB")

    # Store file
    org_dir = UPLOAD_DIR / str(ctx.organization_id) / str(company_id)
    org_dir.mkdir(parents=True, exist_ok=True)

    storage_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = org_dir / storage_name
    storage_path.write_bytes(contents)

    # Create record
    doc = CompanyDocument(
        organization_id=ctx.organization_id,
        company_id=company_id,
        filename=storage_name,
        original_name=file.filename,
        file_size=len(contents),
        mime_type=file.content_type or "application/octet-stream",
        extension=ext,
        storage_path=str(storage_path.relative_to(UPLOAD_DIR)),
        uploaded_by=getattr(ctx, "user_id", None),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    return {
        "id": doc.id, "company_id": doc.company_id,
        "original_name": doc.original_name, "filename": doc.filename,
        "file_size": doc.file_size, "mime_type": doc.mime_type,
        "extension": doc.extension, "created_at": str(doc.created_at),
        "uploaded_by": doc.uploaded_by,
    }


@router.get("/documents")
def list_documents(
    company_id: int = Query(),
    search: str = "",
    sort: str = "newest",
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List documents for a company."""
    stmt = select(CompanyDocument).where(
        CompanyDocument.organization_id == ctx.organization_id,
        CompanyDocument.company_id == company_id,
    )
    if search:
        stmt = stmt.where(CompanyDocument.original_name.ilike(f"%{search}%"))

    sort_map = {
        "newest": CompanyDocument.created_at.desc(),
        "oldest": CompanyDocument.created_at.asc(),
        "name": CompanyDocument.original_name.asc(),
        "size": CompanyDocument.file_size.desc(),
    }
    stmt = stmt.order_by(sort_map.get(sort, CompanyDocument.created_at.desc()))

    docs = session.execute(stmt).scalars().all()
    return {
        "items": [{
            "id": d.id, "company_id": d.company_id,
            "original_name": d.original_name, "filename": d.filename,
            "file_size": d.file_size, "mime_type": d.mime_type,
            "extension": d.extension, "created_at": str(d.created_at),
            "uploaded_by": d.uploaded_by,
        } for d in docs],
        "total": len(docs),
    }


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Download a document."""
    doc = session.execute(
        select(CompanyDocument).where(
            CompanyDocument.id == document_id,
            CompanyDocument.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    file_path = UPLOAD_DIR / doc.storage_path
    if not file_path.exists():
        raise HTTPException(404, "File not found on disk")

    return FileResponse(file_path, filename=doc.original_name, media_type=doc.mime_type)


@router.patch("/documents/{document_id}")
def rename_document(
    document_id: int,
    name: str = Query(),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Rename a document."""
    doc = session.execute(
        select(CompanyDocument).where(
            CompanyDocument.id == document_id,
            CompanyDocument.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    doc.original_name = name
    session.commit()
    return {"id": doc.id, "original_name": doc.original_name}


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Delete a document."""
    doc = session.execute(
        select(CompanyDocument).where(
            CompanyDocument.id == document_id,
            CompanyDocument.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Delete file from disk
    file_path = UPLOAD_DIR / doc.storage_path
    if file_path.exists():
        file_path.unlink()

    session.delete(doc)
    session.commit()
    return {"status": "deleted", "id": document_id}
