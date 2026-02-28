"""Application exceptions for HTTP handling."""


class LearningServiceUnavailableError(Exception):
    """Raised when the LLM or embedding service is rate-limited, out of quota, or unreachable."""

    def __init__(self, message: str = "Learning service temporarily unavailable.", cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause
