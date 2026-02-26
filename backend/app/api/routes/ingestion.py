"""Ingestion pipeline routes: file upload, job management, and progress."""

from __future__ import annotations

import os
import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_or_api_key
from app.models.collection import Collection
from app.models.ingestion_job import IngestionJob
from app.models.user import User
from app.schemas.ingestion import IngestionJobCreate, IngestionJobResponse

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Streaming upload configuration
STREAM_CHUNK_SIZE = 8192  # 8KB chunks for memory-efficient streaming


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file for ingestion",
)
async def upload_file(
    file: UploadFile = File(...),
    collection_id: str = Form(...),
    current_user: User = Depends(get_current_user_or_api_key),
):
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt", ".csv", ".json", ".md"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    # Server-side file size validation
    # Note: file.size may not be available in all cases, so we validate during streaming
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if hasattr(file, 'size') and file.size and file.size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file with streaming to avoid loading entire file into memory
    file_id = str(_uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    total_size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(STREAM_CHUNK_SIZE):
            total_size += len(chunk)
            # Validate size during streaming (in case file.size wasn't available)
            if total_size > max_size_bytes:
                f.close()
                os.remove(file_path)  # Clean up partial file
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
                )
            f.write(chunk)

    return {
        "file_path": file_path,
        "file_name": file.filename,
        "file_size": total_size,
        "file_type": ext.lstrip("."),
        "collection_id": collection_id,
    }


@router.post(
    "/jobs",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ingestion job",
)
async def create_job(
    collection_id: _uuid.UUID,
    payload: IngestionJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    # Verify collection exists
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Collection not found.")

    job = IngestionJob(
        collection_id=collection_id,
        file_path=payload.file_path,
        file_name=payload.file_name,
        file_size=payload.file_size,
        file_type=payload.file_type,
        config=payload.config,
        created_by=current_user.id,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Try to dispatch Celery task
    try:
        from app.workers.tasks import process_ingestion_job
        process_ingestion_job.delay(str(job.id))
    except Exception:
        pass  # Celery not available; job stays pending

    return job


@router.get(
    "/jobs",
    summary="List ingestion jobs",
)
async def list_jobs(
    collection_id: _uuid.UUID | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(IngestionJob)
    count_query = select(func.count(IngestionJob.id))

    if collection_id:
        query = query.where(IngestionJob.collection_id == collection_id)
        count_query = count_query.where(IngestionJob.collection_id == collection_id)
    if status_filter:
        query = query.where(IngestionJob.status == status_filter)
        count_query = count_query.where(IngestionJob.status == status_filter)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(IngestionJob.created_at.desc()).offset(skip).limit(limit)
    )
    jobs = list(result.scalars().all())

    return {"items": jobs, "total": total}


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get job details",
)
async def get_job(
    job_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")
    return job


@router.get(
    "/jobs/{job_id}/progress",
    summary="SSE endpoint for job progress",
)
async def job_progress(
    job_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    import asyncio
    import json

    async def event_generator():
        for _ in range(300):  # Max 5 min
            result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                return

            progress = {
                "job_id": str(job.id),
                "status": job.status,
                "total_chunks": job.total_chunks,
                "processed_chunks": job.processed_chunks,
                "failed_chunks": job.failed_chunks,
                "progress_pct": round(
                    (job.processed_chunks / job.total_chunks * 100) if job.total_chunks > 0 else 0, 1
                ),
            }
            yield f"data: {json.dumps(progress)}\n\n"

            if job.status in ("completed", "failed", "cancelled"):
                return

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a job",
)
async def cancel_job(
    job_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {job.status} job.")

    job.status = "cancelled"
    await db.commit()


@router.post(
    "/jobs/{job_id}/retry",
    response_model=IngestionJobResponse,
    summary="Retry a failed job",
)
async def retry_job(
    job_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried.")

    job.status = "pending"
    job.error_message = None
    job.processed_chunks = 0
    job.failed_chunks = 0
    await db.commit()
    await db.refresh(job)

    try:
        from app.workers.tasks import process_ingestion_job
        process_ingestion_job.delay(str(job.id))
    except Exception:
        pass

    return job


@router.get(
    "/templates",
    summary="List pipeline templates",
)
async def list_templates():
    return [
        {
            "id": "rag",
            "name": "RAG Pipeline",
            "description": "Optimized for retrieval-augmented generation",
            "config": {
                "chunking_strategy": "sentence",
                "chunk_size": 500,
                "chunk_overlap": 50,
            },
        },
        {
            "id": "semantic-search",
            "name": "Semantic Search",
            "description": "Optimized for semantic search applications",
            "config": {
                "chunking_strategy": "fixed_size",
                "chunk_size": 1000,
                "chunk_overlap": 100,
            },
        },
        {
            "id": "faq",
            "name": "FAQ Pipeline",
            "description": "Optimized for question-answer pairs",
            "config": {
                "chunking_strategy": "paragraph",
                "chunk_size": 300,
                "chunk_overlap": 0,
            },
        },
    ]
