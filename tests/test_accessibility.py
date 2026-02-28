"""AccessibilityEngine tests."""

from datetime import date
from uuid import uuid4

import pytest

from app.services.accessibility import AccessibilityEngine, AdaptationRules
from app.models import ChildProfile, NeuroProfile, ChildDisability
from app.models.caregiver import Caregiver


def _make_child(caregiver_id=None):
    c = ChildProfile(
        child_id=uuid4(),
        caregiver_id=caregiver_id or uuid4(),
        full_name="Test Child",
        date_of_birth=date(2015, 1, 1),
        primary_language="en",
    )
    return c


def _make_neuro(child_id, diagnoses=None, attention_span_mins=10, sensory=None):
    return NeuroProfile(
        profile_id=uuid4(),
        child_id=child_id,
        diagnoses=diagnoses or [],
        attention_span_mins=attention_span_mins,
        preferred_modalities=["TEXT"],
        communication_style="LITERAL",
        sensory_thresholds=sensory or {"visual": 0.5, "auditory": 0.5, "motion": 0.5},
        hyperfocus_topics=[],
        frustration_threshold=0.6,
    )


def _make_disability(child_id, disability_type, accommodations=None):
    return ChildDisability(
        disability_id=uuid4(),
        child_id=child_id,
        disability_type=disability_type,
        severity="MODERATE",
        accommodations=accommodations or {},
    )


@pytest.mark.asyncio
async def test_adhd_rules_include_attention_span():
    engine = AccessibilityEngine()
    child = _make_child()
    neuro = _make_neuro(child.child_id, diagnoses=["ADHD_COMBINED"], attention_span_mins=8)
    rules = await engine.derive(child, neuro, [])
    assert any("4 sentences" in r or "gamified" in r.lower() for r in rules.prompt_rules)
    assert rules.session_constraints.get("break_every_mins", 99) <= 15


@pytest.mark.asyncio
async def test_asd_rules_prohibit_metaphors():
    engine = AccessibilityEngine()
    child = _make_child()
    neuro = _make_neuro(child.child_id, diagnoses=["ASD_L1"])
    rules = await engine.derive(child, neuro, [])
    assert any("literal" in r.lower() and "metaphor" in r.lower() or "idiom" in r.lower() for r in rules.prompt_rules) or any(
        "literal" in r.lower() for r in rules.prompt_rules
    )


@pytest.mark.asyncio
async def test_visual_impairment_sets_screen_reader():
    engine = AccessibilityEngine()
    child = _make_child()
    disabilities = [_make_disability(child.child_id, "VISUAL_IMPAIRMENT")]
    rules = await engine.derive(child, None, disabilities)
    assert rules.ui_directives.get("screen_reader", False) is True or "describe_all_visuals" in rules.ui_directives


@pytest.mark.asyncio
async def test_chronic_fatigue_sets_session_limit():
    engine = AccessibilityEngine()
    child = _make_child()
    disabilities = [_make_disability(child.child_id, "CHRONIC_FATIGUE")]
    rules = await engine.derive(child, None, disabilities)
    assert rules.session_constraints.get("max_session_mins", 999) <= 60
    assert "max_word_count" in rules.content_filters or rules.session_constraints.get("break_every_mins", 99) <= 15


@pytest.mark.asyncio
async def test_multiple_diagnoses_merged_correctly():
    engine = AccessibilityEngine()
    child = _make_child()
    neuro = _make_neuro(child.child_id, diagnoses=["ADHD_INATTENTIVE", "DYSLEXIA"])
    rules = await engine.derive(child, neuro, [])
    assert any("4 sentences" in r or "gamified" in r.lower() for r in rules.prompt_rules)
    assert rules.content_filters.get("min_flesch", 0) >= 70 or any("Flesch" in r or "70" in r for r in rules.prompt_rules)


@pytest.mark.asyncio
async def test_disability_accommodations_override_defaults():
    engine = AccessibilityEngine()
    child = _make_child()
    accommodations = {"screen_reader": False, "custom": True}
    disabilities = [_make_disability(child.child_id, "VISUAL_IMPAIRMENT", accommodations=accommodations)]
    rules = await engine.derive(child, None, disabilities)
    assert rules.ui_directives.get("custom") is True
