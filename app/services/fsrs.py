"""FSRS-4.5 spaced repetition service."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.constants import FSRS_W


@dataclass
class FSRSResult:
    stability: float
    difficulty: float
    next_review: datetime
    retrievability: float


class FSRSService:
    """FSRS-4.5 with pretrained default weights W[0..18]."""

    def __init__(self, w: list[float] | None = None):
        self.w = w or FSRS_W

    def initial_review(self, rating: int) -> FSRSResult:
        """First review: rating 1-4 (Again, Hard, Good, Easy)."""
        s = self._init_stability(rating)
        d = self._init_difficulty(rating)
        interval = self._interval(s, 0.9)
        next_review = datetime.now(timezone.utc)
        from datetime import timedelta
        next_review = next_review + timedelta(days=interval)
        return FSRSResult(
            stability=s,
            difficulty=d,
            next_review=next_review,
            retrievability=1.0,
        )

    def review(
        self,
        stability: float,
        difficulty: float,
        last_reviewed: datetime,
        rating: int,
    ) -> FSRSResult:
        """Subsequent review; returns new stability, difficulty, next_review."""
        days_elapsed = (datetime.now(timezone.utc) - last_reviewed).total_seconds() / 86400
        r = self.retrievability(stability, days_elapsed)
        s_new = self._next_stability(stability, difficulty, r, rating)
        d_new = self._next_difficulty(difficulty, rating)
        interval = self._interval(s_new, 0.9)
        from datetime import timedelta
        next_review = datetime.now(timezone.utc) + timedelta(days=interval)
        return FSRSResult(
            stability=s_new,
            difficulty=d_new,
            next_review=next_review,
            retrievability=self.retrievability(s_new, 0),
        )

    def retrievability(self, stability: float, days_elapsed: float) -> float:
        """Decay of retrievability over time."""
        if stability <= 0:
            return 0.0
        return (1 + 0.9 * (days_elapsed / stability)) ** -1

    def _init_stability(self, rating: int) -> float:
        return self.w[rating - 1] if 1 <= rating <= 4 else self.w[0]

    def _init_difficulty(self, rating: int) -> float:
        return 0.3 + 0.1 * (rating - 3)  # simple init

    def _next_stability(self, s: float, d: float, r: float, rating: int) -> float:
        """FSRS-4.5 next stability formula (simplified)."""
        if rating == 1:
            return self.w[0]
        if rating == 2:
            return s * 0.8
        if rating == 3:
            return s * (1 + 0.5 * (1 - r))
        if rating == 4:
            return s * (1 + 1.2 * (1 - r))
        return s

    def _next_difficulty(self, d: float, rating: int) -> float:
        if rating == 1:
            return min(10, d + 0.2)
        if rating == 2:
            return min(10, d + 0.05)
        if rating == 4:
            return max(0.1, d - 0.05)
        return d

    def _interval(self, stability: float, target_retention: float = 0.90) -> int:
        """Days until next review for target retention."""
        if stability <= 0:
            return 1
        from math import log
        return max(1, int(stability * (target_retention ** -1 / 9 - 1)))
