"""Alter embedding column to 768 dims (gemini-embedding-001 / text-embedding-005).

Revision ID: 002
Revises: 001
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("idx_chunks_embedding", table_name="knowledge_chunks")
    op.execute(
        "ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(768) USING NULL"
    )
    op.create_index(
        "idx_chunks_embedding",
        "knowledge_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 256},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_chunks_embedding", table_name="knowledge_chunks")
    op.execute(
        "ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(1536) USING NULL"
    )
    op.create_index(
        "idx_chunks_embedding",
        "knowledge_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 256},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
