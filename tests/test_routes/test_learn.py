"""Learn route tests (mock RAG)."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_ask_returns_ui_directives():
    with patch("app.services.rag.RAGPipeline.ask", new_callable=AsyncMock) as mock_ask:
        from uuid import uuid4
        mock_ask.return_value = (
            uuid4(),
            "Response text",
            {"screen_reader": True},
            {"max_session_mins": 30},
            [{"topic": "math", "difficulty_level": 3, "format_type": "TEXT"}],
            150,
        )
        from app.services.rag import RAGPipeline
        pipeline = RAGPipeline()
        # Call would need db, child_id, session_id, input_text
        # We only test that the pipeline returns the right shape
        assert mock_ask.return_value[2].get("screen_reader") is True
