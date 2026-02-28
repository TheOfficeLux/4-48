"""DynamicPromptBuilder: assemble LLM system prompt from profile, state, chunks, rules."""

from app.models import KnowledgeChunk
from app.models.child import ChildProfile
from app.services.accessibility import AdaptationRules


class DynamicPromptBuilder:
    """Build full LLM system prompt with zero hardcoding."""

    def build(
        self,
        child: ChildProfile,
        state: "AdaptiveState",
        chunks: list[KnowledgeChunk],
        weak_topics: list[str],
        due_topics: list[str],
        adaptation: AdaptationRules,
        neuro_profile: "NeuroProfile | None" = None,
        disabilities: list | None = None,
    ) -> str:
        sections = []
        neuro = neuro_profile
        diagnoses = (neuro.diagnoses or []) if neuro else []
        disabilities = disabilities or []
        age = ""
        if child.date_of_birth:
            from datetime import date
            today = date.today()
            age = str(today.year - child.date_of_birth.year)
        section1 = [
            f"CHILD PROFILE: name={child.full_name}, age={age}, primary_language={child.primary_language}",
            f"Diagnoses: {', '.join(diagnoses) or 'none'}",
            f"Disabilities: {', '.join(getattr(d, 'disability_type', str(d)) for d in disabilities) or 'none'}",
            f"Current cognitive_load={getattr(state, 'cognitive_load', 0.3)}, mood_score={getattr(state, 'mood_score', 0.2)}.",
        ]
        sections.append("\n".join(section1))
        rules = list(adaptation.prompt_rules)
        if getattr(state, "cognitive_load", 0) > 0.75:
            rules.append("CRITICAL: Give the shortest possible answer and offer a break.")
        if getattr(state, "mood_score", 0) < -0.35:
            rules.append("CRITICAL: Open with encouragement; never shame or criticise.")
        if getattr(state, "readiness_score", 0.8) >= 0.9 and neuro and (neuro.hyperfocus_topics or []):
            rules.append("Child may be in hyperfocus; offer depth extension or bonus challenge if relevant.")
        if due_topics:
            rules.append(f"Gentle spaced repetition nudge for topics: {', '.join(due_topics[:3])}.")
        sections.append("BEHAVIORAL RULES:\n" + "\n".join(rules))
        context_lines = []
        for c in chunks[:5]:
            context_lines.append(f"[{c.topic} | difficulty={c.difficulty_level} | {c.format_type}]\n{c.content[:800]}")
        sections.append("KNOWLEDGE CONTEXT:\n" + "\n\n".join(context_lines))
        sections.append(
            "GENERAL INSTRUCTIONS: Respond in the child's primary language. Be supportive. "
            "If the question is out of scope, say you're not sure and suggest they ask their teacher."
        )
        return "\n\n---\n\n".join(sections)
