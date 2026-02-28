"""SignalProcessor + StateService for behavioral signals and adaptive state."""

import math
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    SIG_COGNITIVE_KEYPRESS_WEIGHT,
    SIG_COGNITIVE_KEYPRESS_DIVISOR_MS,
    SIG_COGNITIVE_BACKSPACE_WEIGHT,
    SIG_COGNITIVE_REREAD_WEIGHT,
    SIG_COGNITIVE_HINT_WEIGHT,
    SIG_MOOD_POSITIVE_WEIGHT,
    SIG_MOOD_ABANDON_WEIGHT,
    SIG_MOOD_HINT_WEIGHT,
    READINESS_COGNITIVE_WEIGHT,
    READINESS_MOOD_WEIGHT,
)
from app.models import AdaptiveState, BehavioralSignal, LearningSession


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class SignalProcessor:
    """Map raw behavioral signals → scalar state scores."""

    def aggregate(self, signals: list[dict]) -> dict:
        """
        cognitive_load: sigmoid of (avg_delay/8000)*0.45 + backspace_rate*0.25 + re_read_rate*0.20 + hint_rate*0.10
        mood_score: (pos_reactions*2-1)*0.6 - abandon_rate*0.5 - hint_rate*0.2  [clamped -1..1]
        readiness_score: 1.0 - cognitive_load*0.55 - max(0, -mood_score)*0.45
        """
        by_type: dict[str, list[float]] = {}
        for s in signals:
            t = s.get("signal_type", "")
            v = s.get("value", 0.0)
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(v)
        avg = lambda k: sum(by_type[k]) / len(by_type[k]) if by_type.get(k) else 0.0
        keypress_delay = avg("KEYPRESS_DELAY")
        backspace_rate = avg("BACKSPACE_RATE")
        re_read_rate = avg("RE_READ")
        hint_rate = avg("HINT_REQUESTED")
        abandon_rate = avg("ABANDON")
        pos_reactions = avg("EMOJI_REACTION")
        cognitive_raw = (keypress_delay / SIG_COGNITIVE_KEYPRESS_DIVISOR_MS) * 0.45
        cognitive_raw += backspace_rate * SIG_COGNITIVE_BACKSPACE_WEIGHT
        cognitive_raw += re_read_rate * SIG_COGNITIVE_REREAD_WEIGHT
        cognitive_raw += hint_rate * SIG_COGNITIVE_HINT_WEIGHT
        cognitive_load = max(0, min(1, sigmoid(cognitive_raw)))
        mood_raw = (pos_reactions * 2 - 1) * SIG_MOOD_POSITIVE_WEIGHT - abandon_rate * SIG_MOOD_ABANDON_WEIGHT - hint_rate * SIG_MOOD_HINT_WEIGHT
        mood_score = max(-1, min(1, mood_raw))
        readiness_score = 1.0 - cognitive_load * READINESS_COGNITIVE_WEIGHT - max(0, -mood_score) * READINESS_MOOD_WEIGHT
        readiness_score = max(0, min(1, readiness_score))
        return {
            "cognitive_load": round(cognitive_load, 4),
            "mood_score": round(mood_score, 4),
            "readiness_score": round(readiness_score, 4),
        }


class StateService:
    """Load/update adaptive state; ingest signals."""

    async def load(self, db: AsyncSession, child_id: UUID) -> AdaptiveState | None:
        result = await db.execute(
            select(AdaptiveState)
            .where(AdaptiveState.child_id == child_id)
            .order_by(AdaptiveState.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        child_id: UUID,
        session_id: UUID,
        signals: list[dict],
    ) -> AdaptiveState:
        processor = SignalProcessor()
        agg = processor.aggregate(signals)
        state = AdaptiveState(
            child_id=child_id,
            session_id=session_id,
            cognitive_load=agg["cognitive_load"],
            mood_score=agg["mood_score"],
            readiness_score=agg["readiness_score"],
        )
        db.add(state)
        await db.flush()
        return state

    async def ingest_signal(
        self,
        db: AsyncSession,
        child_id: UUID,
        session_id: UUID,
        signal_type: str,
        value: float,
        raw_payload: dict | None = None,
    ) -> None:
        sig = BehavioralSignal(
            session_id=session_id,
            child_id=child_id,
            signal_type=signal_type,
            value=value,
            raw_payload=raw_payload,
        )
        db.add(sig)
        await db.flush()
