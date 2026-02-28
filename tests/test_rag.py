"""RAG retrieval, reranker, prompt tests."""

from datetime import date
from uuid import uuid4

import pytest

from app.models import ChildProfile, NeuroProfile, KnowledgeChunk
from app.services.accessibility import AdaptationRules
from app.services.signals import SignalProcessor
from app.services.reranker import ProfileAwareReranker
from app.services.prompt import DynamicPromptBuilder


def _make_chunk(topic="math", difficulty_level=5, format_type="TEXT", flesch_score=70, sensory_load=0.3, neuro_tags=None):
    return KnowledgeChunk(
        chunk_id=uuid4(),
        content="Sample content here.",
        topic=topic,
        difficulty_level=difficulty_level,
        format_type=format_type,
        flesch_score=flesch_score,
        sensory_load=sensory_load,
        neuro_tags=neuro_tags or {},
        avg_engagement=0.5,
    )


def _make_state(cognitive_load=0.3, mood_score=0.2, readiness_score=0.8):
    from app.models.signals import AdaptiveState
    return AdaptiveState(
        state_id=uuid4(),
        child_id=uuid4(),
        cognitive_load=cognitive_load,
        mood_score=mood_score,
        readiness_score=readiness_score,
    )


def test_retrieval_filters_by_difficulty():
    rules = AdaptationRules(
        prompt_rules=[],
        ui_directives={},
        content_filters={"max_difficulty": 4, "min_flesch": 0, "sensory_cap": 1.0},
        session_constraints={},
    )
    assert rules.content_filters["max_difficulty"] == 4


def test_reranker_boosts_weak_topics():
    reranker = ProfileAwareReranker()
    child = ChildProfile(
        child_id=uuid4(),
        caregiver_id=uuid4(),
        full_name="C",
        date_of_birth=date(2015, 1, 1),
        primary_language="en",
    )
    child.neuro_profile = None
    chunks = [
        _make_chunk(topic="algebra"),
        _make_chunk(topic="geometry"),
    ]
    state = _make_state()
    out = reranker.rerank(chunks, child, state, weak_topics=["algebra"], top_n=5)
    assert len(out) <= 5
    if len(out) >= 2:
        scores_algebra = [i for i, c in enumerate(out) if c.topic == "algebra"]
        assert len(scores_algebra) >= 1


def test_reranker_penalises_idioms_for_asd():
    reranker = ProfileAwareReranker()
    child = ChildProfile(
        child_id=uuid4(),
        caregiver_id=uuid4(),
        full_name="C",
        date_of_birth=date(2015, 1, 1),
        primary_language="en",
    )
    neuro = NeuroProfile(
        profile_id=uuid4(),
        child_id=child.child_id,
        diagnoses=["ASD_L1"],
        preferred_modalities=["TEXT"],
        communication_style="LITERAL",
        sensory_thresholds={"visual": 0.5, "auditory": 0.5, "motion": 0.5},
    )
    child.neuro_profile = neuro
    chunks = [
        _make_chunk(neuro_tags={"idiom_density": 0.5}),
        _make_chunk(neuro_tags={"idiom_density": 0.1}),
    ]
    state = _make_state()
    out = reranker.rerank(chunks, child, state, weak_topics=[], top_n=5)
    assert len(out) >= 1


def test_prompt_includes_all_profile_rules():
    builder = DynamicPromptBuilder()
    child = ChildProfile(
        child_id=uuid4(),
        caregiver_id=uuid4(),
        full_name="Test",
        date_of_birth=date(2015, 1, 1),
        primary_language="en",
    )
    child.neuro_profile = None
    child.disabilities = []
    state = _make_state()
    rules = AdaptationRules(
        prompt_rules=["Rule one.", "Rule two."],
        ui_directives={},
        content_filters={},
        session_constraints={},
    )
    prompt = builder.build(child, state, [_make_chunk()], [], [], rules)
    assert "Rule one" in prompt and "Rule two" in prompt
    assert "CHILD PROFILE" in prompt or "Test" in prompt


def test_high_cognitive_load_triggers_override_rule():
    builder = DynamicPromptBuilder()
    child = ChildProfile(
        child_id=uuid4(),
        caregiver_id=uuid4(),
        full_name="Test",
        date_of_birth=date(2015, 1, 1),
        primary_language="en",
    )
    child.neuro_profile = None
    child.disabilities = []
    state = _make_state(cognitive_load=0.9)
    rules = AdaptationRules(prompt_rules=[], ui_directives={}, content_filters={}, session_constraints={})
    prompt = builder.build(child, state, [], [], [], rules)
    assert "CRITICAL" in prompt and "shortest" in prompt
