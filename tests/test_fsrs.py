"""FSRS service tests."""

from datetime import datetime, timezone, timedelta

import pytest

from app.services.fsrs import FSRSService, FSRSResult


def test_initial_review_rating_1_low_stability():
    fsrs = FSRSService()
    res = fsrs.initial_review(1)
    assert isinstance(res, FSRSResult)
    assert res.stability <= 2.0


def test_initial_review_rating_4_high_stability():
    fsrs = FSRSService()
    res = fsrs.initial_review(4)
    assert res.stability >= res.difficulty


def test_subsequent_review_increases_interval():
    fsrs = FSRSService()
    res1 = fsrs.initial_review(4)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    res2 = fsrs.review(res1.stability, res1.difficulty, past, 4)
    assert res2.next_review > datetime.now(timezone.utc)


def test_forgetting_resets_stability():
    fsrs = FSRSService()
    res = fsrs.initial_review(3)
    long_ago = datetime.now(timezone.utc) - timedelta(days=365)
    res2 = fsrs.review(res.stability, res.difficulty, long_ago, 1)
    assert res2.stability <= res.stability or res2.stability < 2.0


def test_mastery_level_approaches_1_after_many_good_reviews():
    fsrs = FSRSService()
    res = fsrs.initial_review(4)
    now = datetime.now(timezone.utc)
    for _ in range(5):
        res = fsrs.review(res.stability, res.difficulty, now, 4)
        now = res.next_review
    assert res.stability > 1.0
