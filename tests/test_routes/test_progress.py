"""Progress route tests."""

import pytest


def test_progress_schemas():
    from app.schemas.progress import ProgressDashboardResponse, MasteryRecordResponse
    from uuid import uuid4
    uid = uuid4()
    r = ProgressDashboardResponse(
        child_id=uid,
        mastery_records=[],
        total_sessions=0,
        total_interactions=0,
    )
    assert r.child_id == uid
    assert r.total_sessions == 0
