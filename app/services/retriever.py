"""HybridRetriever: pgvector cosine + BM25 tsvector."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import RAG_HYBRID_VECTOR_WEIGHT, RAG_HYBRID_BM25_WEIGHT
from app.models import KnowledgeChunk
from app.services.accessibility import AdaptationRules


class HybridRetriever:
    """Hybrid search with pre-filters from AdaptationRules."""

    async def retrieve(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        child_input: str,
        state: "AdaptiveState",
        rules: AdaptationRules,
        top_k: int = 20,
    ) -> list[KnowledgeChunk]:
        filters = rules.content_filters
        max_difficulty = filters.get("max_difficulty", 10)
        readiness = 0.8
        if state is not None:
            r = getattr(state, "readiness_score", None)
            if r is not None:
                try:
                    readiness = float(r)
                except (TypeError, ValueError):
                    pass
        readiness = max(0.0, min(1.0, readiness))
        max_difficulty = min(max_difficulty, max(1, round(readiness * 10)))
        min_flesch = filters.get("min_flesch", 0)
        sensory_cap = filters.get("sensory_cap", 1.0)
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        query_safe = (child_input or "")[:500].replace("'", "''")
        sql = text("""
            SELECT chunk_id FROM knowledge_chunks k
            WHERE k.difficulty_level <= :max_diff
            AND k.sensory_load <= :sensory_cap
            AND k.flesch_score >= :min_flesch
            AND k.embedding IS NOT NULL
            ORDER BY (1 - (k.embedding <=> CAST(:vec AS vector))) * :w1
                + COALESCE(ts_rank(to_tsvector('english', k.content), plainto_tsquery('english', :query)), 0) * :w2 DESC
            LIMIT :top_k
        """)
        result = await db.execute(
            sql,
            {
                "vec": vec_str,
                "w1": RAG_HYBRID_VECTOR_WEIGHT,
                "w2": RAG_HYBRID_BM25_WEIGHT,
                "query": query_safe,
                "max_diff": max_difficulty,
                "sensory_cap": sensory_cap,
                "min_flesch": min_flesch,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()
        if not rows:
            result2 = await db.execute(
                select(KnowledgeChunk)
                .where(KnowledgeChunk.difficulty_level <= max_difficulty)
                .where(KnowledgeChunk.flesch_score >= min_flesch)
                .limit(top_k)
            )
            return list(result2.scalars().all())
        chunk_ids = [row[0] for row in rows]
        result3 = await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.chunk_id.in_(chunk_ids)))
        chunks = {c.chunk_id: c for c in result3.scalars().all()}
        return [chunks[cid] for cid in chunk_ids if cid in chunks]