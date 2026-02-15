"""Celery tasks for background processing."""

from __future__ import annotations

import hashlib
import traceback
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.utils.logger import logger


@celery_app.task(bind=True, name="app.workers.tasks.process_ingestion_job")
def process_ingestion_job(self, job_id: str):
    """Process an ingestion job: parse document, chunk text, generate embeddings, insert vectors."""
    from app.database import sync_session_maker
    from app.models.ingestion_job import IngestionJob
    from app.models.vector import VectorRecord
    from app.models.collection import Collection
    from app.utils.parsers import parse_document
    from app.utils.chunking import get_chunker

    logger.info("Starting ingestion job {}", job_id)

    session = sync_session_maker()
    try:
        job = session.query(IngestionJob).filter_by(id=job_id).first()
        if job is None:
            logger.error("Job {} not found", job_id)
            return {"status": "error", "message": "Job not found"}

        if job.status == "cancelled":
            return {"status": "cancelled"}

        # Update status to processing
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        session.commit()

        # Get collection info
        collection = session.query(Collection).filter_by(id=job.collection_id).first()
        if collection is None:
            job.status = "failed"
            job.error_message = "Collection not found"
            session.commit()
            return {"status": "error", "message": "Collection not found"}

        # Parse document
        try:
            text_content = parse_document(job.file_path, job.file_type or "txt")
        except Exception as e:
            job.status = "failed"
            job.error_message = f"Failed to parse document: {str(e)}"
            session.commit()
            return {"status": "error", "message": str(e)}

        if not text_content or not text_content.strip():
            job.status = "failed"
            job.error_message = "Document is empty or could not be parsed"
            session.commit()
            return {"status": "error", "message": "Empty document"}

        # Chunk text
        config = job.config or {}
        strategy = config.get("chunking_strategy", "fixed_size")
        chunk_size = config.get("chunk_size", 500)
        chunk_overlap = config.get("chunk_overlap", 50)

        chunker = get_chunker(strategy)
        chunks = chunker(text_content, chunk_size=chunk_size, overlap=chunk_overlap)

        job.total_chunks = len(chunks)
        session.commit()

        logger.info("Job {}: {} chunks to process", job_id, len(chunks))

        # Process chunks in batches
        batch_size = 50
        dimension = collection.dimension

        for i in range(0, len(chunks), batch_size):
            if job.status == "cancelled":
                break

            batch = chunks[i : i + batch_size]

            for idx, chunk_text in enumerate(batch):
                try:
                    # Generate a deterministic mock vector based on text content
                    # In production, this would call an embedding provider
                    import numpy as np
                    seed = int(hashlib.md5(chunk_text.encode()).hexdigest()[:8], 16)
                    rng = np.random.RandomState(seed)
                    vector = rng.randn(dimension).astype(float).tolist()
                    # Normalize
                    norm = sum(v * v for v in vector) ** 0.5
                    vector = [v / norm for v in vector]

                    fingerprint = hashlib.sha256(chunk_text.encode()).hexdigest()

                    record = VectorRecord(
                        collection_id=collection.id,
                        vector=vector,
                        metadata_={"source": job.file_name, "chunk_index": i + idx},
                        text_content=chunk_text,
                        source_file=job.file_name,
                        chunk_index=i + idx,
                        fingerprint=fingerprint,
                    )
                    session.add(record)
                    job.processed_chunks += 1
                except Exception as e:
                    logger.error("Failed to process chunk {}: {}", i + idx, e)
                    job.failed_chunks += 1

            session.commit()

        # Complete
        job.status = "completed" if job.failed_chunks == 0 else "completed"
        job.completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            "Job {} completed: {}/{} chunks processed, {} failed",
            job_id,
            job.processed_chunks,
            job.total_chunks,
            job.failed_chunks,
        )

        return {
            "status": "completed",
            "processed": job.processed_chunks,
            "failed": job.failed_chunks,
            "total": job.total_chunks,
        }

    except Exception as e:
        logger.error("Job {} failed: {}", job_id, traceback.format_exc())
        try:
            job = session.query(IngestionJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                session.commit()
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
    finally:
        session.close()
