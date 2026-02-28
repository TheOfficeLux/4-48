"""RAGPipeline: orchestrate embed -> retrieve -> rerank -> prompt -> LLM."""

import hashlib
import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChildProfile, NeuroProfile, ChildDisability, AdaptiveState, Interaction, LearningSession, MasteryRecord
from app.services.accessibility import AccessibilityEngine, AdaptationRules
from app.services.embeddings import EmbeddingService
from app.services.retriever import HybridRetriever
from app.services.reranker import ProfileAwareReranker
from app.services.prompt import DynamicPromptBuilder
from app.config import get_settings
from app.redis_client import get_redis
from app.constants import CACHE_STATE_TTL, CACHE_MASTERY_WEAK_TTL
from app.exceptions import LearningServiceUnavailableError

logger = structlog.get_logger()

# Shown to the child when OpenAI is rate-limited, out of quota, or unreachable
FALLBACK_RESPONSE = (
    "I'm having a little trouble right now. Please try again in a minute, "
    "or ask your grown-up for help."
)


class RAGPipeline:
    """Orchestrate retrieval, rerank, prompt build, and LLM call."""

    def __init__(self):
        self.embedding_svc = EmbeddingService()
        self.retriever = HybridRetriever()
        self.reranker = ProfileAwareReranker()
        self.prompt_builder = DynamicPromptBuilder()
        self.accessibility = AccessibilityEngine()
        self.settings = get_settings()

    async def ask(
        self,
        db: AsyncSession,
        child_id: UUID,
        session_id: UUID,
        input_text: str,
        input_type: str = "TEXT",
    ) -> tuple[UUID, str, dict, dict, list[dict], int]:
        """
        Returns (interaction_id, response_text, ui_directives, session_constraints, chunks_used, response_time_ms).
        """
        start_ms = int(time.time() * 1000)
        child_result = await db.execute(
            select(ChildProfile).where(ChildProfile.child_id == child_id)
        )
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Child not found")
        np_result = await db.execute(select(NeuroProfile).where(NeuroProfile.child_id == child_id))
        neuro = np_result.scalar_one_or_none()
        d_result = await db.execute(select(ChildDisability).where(ChildDisability.child_id == child_id))
        disabilities = list(d_result.scalars().all())
        rules = await self.accessibility.derive(child, neuro, disabilities)
        state_result = await db.execute(
            select(AdaptiveState)
            .where(AdaptiveState.child_id == child_id)
            .order_by(AdaptiveState.recorded_at.desc())
            .limit(1)
        )
        state = state_result.scalar_one_or_none()
        if not state:
            state = AdaptiveState(child_id=child_id, session_id=session_id)
        weak_topics = await self._weak_topics(db, child_id)
        due_topics = await self._due_topics(db, child_id)

        try:
            query_embedding = await self.embedding_svc.embed(input_text)
            chunks = await self.retriever.retrieve(
                db, query_embedding, input_text, state, rules, top_k=self.settings.rag_retrieve_top_k
            )
            chunks = self.reranker.rerank(
                chunks, child, state, weak_topics,
                neuro_profile=neuro, disabilities=disabilities,
                top_n=self.settings.rag_rerank_top_n,
            )
            system_prompt = self.prompt_builder.build(
                child, state, chunks, weak_topics, due_topics, rules,
                neuro_profile=neuro, disabilities=disabilities,
            )
            response_text = await self._call_llm(system_prompt, input_text)
            chunk_ids = [c.chunk_id for c in chunks]
            chunks_used = [{"topic": c.topic, "difficulty_level": c.difficulty_level, "format_type": c.format_type} for c in chunks]
        except LearningServiceUnavailableError as e:
            logger.warning("openai_unavailable", reason=str(e.cause) if getattr(e, "cause", None) else str(e))
            response_text = FALLBACK_RESPONSE
            chunk_ids = []
            chunks_used = []

        response_time_ms = int(time.time() * 1000) - start_ms
        prompt_hash = hashlib.md5((response_text or "").encode()).hexdigest()[:16]
        interaction = Interaction(
            session_id=session_id,
            child_id=child_id,
            input_text=input_text,
            input_type=input_type,
            response_text=response_text,
            retrieved_chunk_ids=chunk_ids,
            llm_prompt_hash=prompt_hash,
            response_time_ms=response_time_ms,
        )
        db.add(interaction)
        await db.flush()
        session_result = await db.execute(select(LearningSession).where(LearningSession.session_id == session_id))
        sess = session_result.scalar_one_or_none()
        if sess:
            sess.total_interactions = (sess.total_interactions or 0) + 1
            await db.flush()
        return interaction.interaction_id, response_text, rules.ui_directives, rules.session_constraints, chunks_used, response_time_ms

    def _get_llm_client(self):
        """Return the chat LLM client (Mistral or OpenAI) based on config."""
        from openai import AsyncOpenAI

        if self.settings.llm_provider == "mistral":
            return AsyncOpenAI(
                base_url="https://api.mistral.ai/v1",
                api_key=self.settings.mistral_api_key,
            )
        return AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        import asyncio
        from openai import APIError, RateLimitError

        from app.exceptions import LearningServiceUnavailableError

        client = self._get_llm_client()
        for attempt in range(3):
            try:
                resp = await client.chat.completions.create(
                    model=self.settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=self.settings.llm_max_tokens,
                    temperature=self.settings.llm_temperature,
                )
                return resp.choices[0].message.content or ""
            except RateLimitError as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LearningServiceUnavailableError(
                    "Learning assistant is temporarily unavailable (rate limit or quota). Please try again in a few minutes.",
                    cause=e,
                ) from e
            except (APIError, Exception) as e:
                raise LearningServiceUnavailableError(
                    "Learning assistant is temporarily unavailable. Please try again later.",
                    cause=e,
                ) from e

    async def _weak_topics(self, db: AsyncSession, child_id: UUID) -> list[str]:
        redis = get_redis()
        if redis:
            try:
                import json
                raw = await redis.get(f"mastery:weak:{child_id}")
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
        result = await db.execute(
            select(MasteryRecord.topic).where(
                MasteryRecord.child_id == child_id,
                MasteryRecord.mastery_level < 0.5,
            )
        )
        topics = [r[0] for r in result.fetchall()]
        if redis:
            try:
                import json
                await redis.set(f"mastery:weak:{child_id}", json.dumps(topics), ex=CACHE_MASTERY_WEAK_TTL)
            except Exception:
                pass
        return topics

    async def _due_topics(self, db: AsyncSession, child_id: UUID) -> list[str]:
        from datetime import datetime, timezone
        result = await db.execute(
            select(MasteryRecord.topic).where(
                MasteryRecord.child_id == child_id,
                MasteryRecord.next_review_due <= datetime.now(timezone.utc),
            )
        )
        return [r[0] for r in result.fetchall()]