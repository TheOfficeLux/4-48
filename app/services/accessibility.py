"""AccessibilityEngine: derives AdaptationRules from child profile (neuro + disabilities)."""

from dataclasses import dataclass
from uuid import UUID
import json

from app.models import ChildProfile
from app.models.child import NeuroProfile, ChildDisability
from app.constants import CACHE_ADAPTATION_TTL

# Redis for caching (use app.redis_client.get_redis elsewhere)
from app.redis_client import get_redis


@dataclass
class AdaptationRules:
    prompt_rules: list[str]
    ui_directives: dict
    content_filters: dict
    session_constraints: dict


class AccessibilityEngine:
    """Derive ALL adaptation rules from child's neuro_profile + disabilities. Cached in Redis 30 min."""

    async def derive(self, child: ChildProfile, neuro: NeuroProfile | None, disabilities: list[ChildDisability]) -> AdaptationRules:
        """Derive rules from profile. Use cache if available."""
        redis = get_redis()
        if redis:
            try:
                raw = await redis.get(f"adaptation:{child.child_id}")
                if raw:
                    data = json.loads(raw)
                    return AdaptationRules(
                        prompt_rules=data["prompt_rules"],
                        ui_directives=data["ui_directives"],
                        content_filters=data["content_filters"],
                        session_constraints=data["session_constraints"],
                    )
            except Exception:
                pass
        rules = self._derive_impl(child, neuro, disabilities)
        if redis:
            try:
                await redis.set(
                    f"adaptation:{child.child_id}",
                    json.dumps({
                        "prompt_rules": rules.prompt_rules,
                        "ui_directives": rules.ui_directives,
                        "content_filters": rules.content_filters,
                        "session_constraints": rules.session_constraints,
                    }),
                    ex=CACHE_ADAPTATION_TTL,
                )
            except Exception:
                pass
        return rules

    def _derive_impl(
        self,
        child: ChildProfile,
        neuro: NeuroProfile | None,
        disabilities: list[ChildDisability],
    ) -> AdaptationRules:
        prompt_rules: list[str] = []
        ui_directives: dict = {}
        content_filters: dict = {"max_difficulty": 10, "min_flesch": 0, "allowed_formats": None, "sensory_cap": 1.0}
        session_constraints: dict = {"max_session_mins": 60, "break_every_mins": 15, "time_factor": 1.0}

        diagnoses = (neuro.diagnoses or []) if neuro else []
        modalities = (neuro.preferred_modalities or ["TEXT"]) if neuro else []
        sensory = (neuro.sensory_thresholds or {}) if neuro else {}
        attention_mins = neuro.attention_span_mins if neuro else 10
        comm_style = (neuro.communication_style or "LITERAL") if neuro else "LITERAL"
        frustration = neuro.frustration_threshold if neuro else 0.6

        # Diagnosis-derived rules
        if any(d.startswith("ADHD") for d in diagnoses):
            prompt_rules.append("Use at most 4 sentences per response.")
            prompt_rules.append("Use gamified framing and one clear next action.")
            session_constraints["break_every_mins"] = min(session_constraints["break_every_mins"], 10)
        if any(d.startswith("ASD") for d in diagnoses):
            prompt_rules.append("Use literal language only; no metaphors or idioms.")
            prompt_rules.append("State the goal first, then give predictable structure.")
            prompt_rules.append("Avoid open-ended questions; prefer clear choices.")
        if "DYSLEXIA" in diagnoses:
            prompt_rules.append("Keep Flesch readability >= 70; use numbered steps only; no long passages.")
            content_filters["min_flesch"] = max(content_filters.get("min_flesch", 0), 70)
        if "DYSCALCULIA" in diagnoses:
            prompt_rules.append("Always provide visual representations for maths; step-by-step only.")
        if "SPD" in diagnoses:
            vis = sensory.get("visual", 0.5)
            content_filters["sensory_cap"] = min(content_filters.get("sensory_cap", 1.0), vis + 0.1)
            prompt_rules.append(f"Cap sensory load to child's visual threshold ({vis}).")
            if vis < 0.4:
                ui_directives["no_emojis"] = True
        if "ANXIETY" in diagnoses:
            prompt_rules.append("Use warm, reassuring tone; no time pressure; set explicit expectations.")

        # Disability-derived rules
        for d in disabilities:
            t = d.disability_type
            acc = d.accommodations or {}
            if t == "VISUAL_IMPAIRMENT":
                ui_directives["screen_reader"] = acc.get("screen_reader", True)
                ui_directives["describe_all_visuals"] = True
                ui_directives["no_color_only_cues"] = True
            elif t == "HEARING_IMPAIRMENT":
                content_filters["exclude_audio"] = True
                ui_directives["captions"] = True
                ui_directives["text_only_mode"] = True
            elif t == "MOTOR_IMPAIRMENT":
                ui_directives["large_targets"] = acc.get("large_targets", True)
                ui_directives["keyboard_only"] = True
                session_constraints["time_factor"] = max(session_constraints.get("time_factor", 1.0), 2.0)
            elif t == "COGNITIVE_DISABILITY":
                content_filters["max_difficulty"] = min(content_filters.get("max_difficulty", 10), 4)
                content_filters["min_flesch"] = max(content_filters.get("min_flesch", 0), 70)
                prompt_rules.append("One instruction at a time.")
            elif t == "SPEECH_IMPAIRMENT":
                ui_directives["no_voice_input_required"] = True
                ui_directives["text_or_selection_only"] = True
            elif t == "CHRONIC_FATIGUE":
                session_constraints["max_session_mins"] = min(session_constraints.get("max_session_mins", 60), 20)
                session_constraints["break_every_mins"] = min(session_constraints.get("break_every_mins", 15), 5)
                content_filters["max_word_count"] = 100

        # Merge disability accommodations into ui_directives
        for d in disabilities:
            for k, v in (d.accommodations or {}).items():
                ui_directives[k] = v

        return AdaptationRules(
            prompt_rules=prompt_rules,
            ui_directives=ui_directives,
            content_filters=content_filters,
            session_constraints=session_constraints,
        )
