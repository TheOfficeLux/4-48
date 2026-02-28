"""POST /admin/ingest — content ingestion for RAG corpus."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_required
from app.models import Caregiver
from app.models import KnowledgeChunk
from app.schemas.admin import IngestRequest, IngestResponse
from app.services.embeddings import EmbeddingService

router = APIRouter()
embedding_svc = EmbeddingService()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_content(
    body: IngestRequest,
    request: Request,
    current_user: Caregiver = Depends(get_current_user_required),
):
    db: AsyncSession = request.state.db
    embedding = await embedding_svc.embed(body.content)
    chunk = KnowledgeChunk(
        content=body.content,
        embedding=embedding,
        topic=body.topic,
        subject_area=body.subject_area,
        difficulty_level=body.difficulty_level,
        format_type=body.format_type,
        flesch_score=body.flesch_score,
        neuro_tags=body.neuro_tags,
        sensory_load=body.sensory_load,
    )
    db.add(chunk)
    await db.flush()
    return IngestResponse(chunk_id=chunk.chunk_id)
