"""ProfileAwareReranker: score adjustments from profile and state."""

from app.constants import (
    RERANK_PREFERRED_MODALITY_BONUS,
    RERANK_FLESCH_TARGET_BASE,
    RERANK_FLESCH_COGNITIVE_FACTOR,
    RERANK_FLESCH_PENALTY_PER_POINT,
    RERANK_ASD_IDIOM_PENALTY,
    RERANK_ASD_IDIOM_THRESHOLD,
    RERANK_ADHD_EXERCISE_BONUS,
    RERANK_ADHD_WORD_PENALTY,
    RERANK_ADHD_WORD_THRESHOLD,
    RERANK_DYSLEXIA_FLESCH_BONUS,
    RERANK_DYSLEXIA_FLESCH_MIN,
    RERANK_WEAK_TOPIC_BONUS,
    RERANK_ENGAGEMENT_BONUS,
    RERANK_ENGAGEMENT_THRESHOLD,
    RERANK_SENSORY_PENALTY_FACTOR,
    RERANK_SENSORY_THRESHOLD_FACTOR,
)
from app.models import KnowledgeChunk
from app.models.child import ChildProfile, NeuroProfile


class ProfileAwareReranker:
    """Rerank chunks with bonuses/penalties from child profile and state."""

    def rerank(
        self,
        chunks: list[KnowledgeChunk],
        child: ChildProfile,
        state: "AdaptiveState",
        weak_topics: list[str],
        neuro_profile: "NeuroProfile | None" = None,
        disabilities: list | None = None,
        top_n: int = 5,
    ) -> list[KnowledgeChunk]:
        diagnoses = []
        preferred_modalities = ["TEXT"]
        sensory_visual = 0.5
        np = neuro_profile
        if np:
            diagnoses = np.diagnoses or []
            preferred_modalities = np.preferred_modalities or ["TEXT"]
            sensory_visual = (np.sensory_thresholds or {}).get("visual", 0.5)
        scored: list[tuple[float, KnowledgeChunk]] = []
        for c in chunks:
            score = 0.0
            if c.format_type in preferred_modalities:
                score += RERANK_PREFERRED_MODALITY_BONUS
            target_flesch = RERANK_FLESCH_TARGET_BASE - getattr(state, "cognitive_load", 0.3) * RERANK_FLESCH_COGNITIVE_FACTOR
            if c.flesch_score < target_flesch:
                score -= (target_flesch - c.flesch_score) * RERANK_FLESCH_PENALTY_PER_POINT
            if any(d.startswith("ASD") for d in diagnoses):
                idiom = (c.neuro_tags or {}).get("idiom_density", 0)
                if idiom > RERANK_ASD_IDIOM_THRESHOLD:
                    score -= RERANK_ASD_IDIOM_PENALTY
            if any(d.startswith("ADHD") for d in diagnoses):
                if c.format_type in ("EXERCISE", "QUIZ"):
                    score += RERANK_ADHD_EXERCISE_BONUS
                wc = (c.neuro_tags or {}).get("word_count", 0)
                if wc > RERANK_ADHD_WORD_THRESHOLD:
                    score -= RERANK_ADHD_WORD_PENALTY
            if "DYSLEXIA" in diagnoses and c.flesch_score >= RERANK_DYSLEXIA_FLESCH_MIN:
                score += RERANK_DYSLEXIA_FLESCH_BONUS
            if c.topic in weak_topics:
                score += RERANK_WEAK_TOPIC_BONUS
            if (c.avg_engagement or 0) > RERANK_ENGAGEMENT_THRESHOLD:
                score += RERANK_ENGAGEMENT_BONUS
            if c.sensory_load > sensory_visual * RERANK_SENSORY_THRESHOLD_FACTOR:
                score *= (1 - RERANK_SENSORY_PENALTY_FACTOR)
            scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:top_n]]
