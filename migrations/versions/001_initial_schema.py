"""Initial schema: enums, caregivers, child_profiles, neuro_profiles, child_disabilities, learning_sessions, adaptive_state, behavioral_signals, knowledge_chunks, interactions, mastery_records.

Revision ID: 001
Revises:
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL native enums
    op.execute("""
        CREATE TYPE diagnosis_type AS ENUM (
            'ADHD_COMBINED', 'ADHD_INATTENTIVE', 'ADHD_HYPERACTIVE',
            'ASD_L1', 'ASD_L2', 'ASD_L3',
            'DYSLEXIA', 'DYSCALCULIA', 'DYSPRAXIA', 'ANXIETY', 'SPD'
        )
    """)
    op.execute("""
        CREATE TYPE disability_type AS ENUM (
            'VISUAL_IMPAIRMENT', 'HEARING_IMPAIRMENT', 'MOTOR_IMPAIRMENT',
            'COGNITIVE_DISABILITY', 'SPEECH_IMPAIRMENT', 'CHRONIC_FATIGUE'
        )
    """)
    op.execute("""
        CREATE TYPE modality_type AS ENUM (
            'VISUAL', 'AUDITORY', 'KINESTHETIC', 'TEXT', 'VIDEO', 'INTERACTIVE'
        )
    """)
    op.execute("""
        CREATE TYPE content_format AS ENUM (
            'EXPLANATION', 'STORY', 'QUIZ', 'DIAGRAM',
            'VIDEO_TRANSCRIPT', 'WORKED_EXAMPLE', 'ANALOGY', 'EXERCISE'
        )
    """)
    op.execute("""
        CREATE TYPE signal_type AS ENUM (
            'KEYPRESS_DELAY', 'BACKSPACE_RATE', 'SCROLL_SPEED',
            'ABANDON', 'RE_READ', 'EMOJI_REACTION', 'VOICE_HESITATION',
            'HINT_REQUESTED', 'SKIP_REQUESTED'
        )
    """)

    # caregivers
    op.create_table(
        "caregivers",
        sa.Column("caregiver_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(50), server_default="parent", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("caregiver_id"),
        sa.UniqueConstraint("email"),
    )

    # child_profiles
    op.create_table(
        "child_profiles",
        sa.Column("child_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("caregiver_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("primary_language", sa.String(10), server_default="en", nullable=False),
        sa.Column("grade_level", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["caregiver_id"], ["caregivers.caregiver_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("child_id"),
    )

    # neuro_profiles
    op.create_table(
        "neuro_profiles",
        sa.Column("profile_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("diagnoses", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("attention_span_mins", sa.Integer(), server_default="10", nullable=False),
        sa.Column("preferred_modalities", sa.ARRAY(sa.String()), server_default="{TEXT}", nullable=False),
        sa.Column("communication_style", sa.String(30), server_default="LITERAL", nullable=False),
        sa.Column("sensory_thresholds", sa.JSON(), server_default='{"visual":0.5,"auditory":0.5,"motion":0.5}', nullable=False),
        sa.Column("ui_preferences", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("hyperfocus_topics", sa.ARRAY(sa.Text()), server_default="{}", nullable=True),
        sa.Column("frustration_threshold", sa.Float(), server_default="0.6", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("child_id"),
    )

    # child_disabilities
    op.create_table(
        "child_disabilities",
        sa.Column("disability_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("disability_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), server_default="MODERATE", nullable=False),
        sa.Column("accommodations", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("disability_id"),
        sa.UniqueConstraint("child_id", "disability_type", name="uq_child_disability_type"),
    )
    op.execute("ALTER TABLE child_disabilities ALTER COLUMN disability_type TYPE disability_type USING disability_type::disability_type")

    # learning_sessions
    op.create_table(
        "learning_sessions",
        sa.Column("session_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_interactions", sa.Integer(), server_default="0", nullable=True),
        sa.Column("avg_response_time_ms", sa.Integer(), nullable=True),
        sa.Column("frustration_events", sa.Integer(), server_default="0", nullable=True),
        sa.Column("hyperfocus_flag", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("session_quality", sa.Float(), nullable=True),
        sa.Column("topics_covered", sa.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )

    # adaptive_state
    op.create_table(
        "adaptive_state",
        sa.Column("state_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("cognitive_load", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("mood_score", sa.Float(), server_default="0.2", nullable=False),
        sa.Column("readiness_score", sa.Float(), server_default="0.8", nullable=False),
        sa.Column("current_topic", sa.String(100), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("cognitive_load >= 0 AND cognitive_load <= 1", name="adaptive_state_cognitive_load_check"),
        sa.CheckConstraint("mood_score >= -1 AND mood_score <= 1", name="adaptive_state_mood_score_check"),
        sa.CheckConstraint("readiness_score >= 0 AND readiness_score <= 1", name="adaptive_state_readiness_score_check"),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"]),
        sa.PrimaryKeyConstraint("state_id"),
    )
    op.create_index("idx_adaptive_state_child", "adaptive_state", ["child_id", "recorded_at"], postgresql_ops={"recorded_at": "DESC"})

    # behavioral_signals (hypertable: PK must include partitioning column ts)
    op.create_table(
        "behavioral_signals",
        sa.Column("signal_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"]),
        sa.PrimaryKeyConstraint("signal_id", "ts"),
    )
    op.execute("ALTER TABLE behavioral_signals ALTER COLUMN signal_type TYPE signal_type USING signal_type::signal_type")
    op.execute("SELECT create_hypertable('behavioral_signals', 'ts', chunk_time_interval => INTERVAL '1 hour')")

    # knowledge_chunks (pgvector)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_chunks",
        sa.Column("chunk_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("subject_area", sa.String(100), nullable=True),
        sa.Column("difficulty_level", sa.Integer(), nullable=False),
        sa.Column("format_type", sa.String(50), nullable=False),
        sa.Column("flesch_score", sa.Float(), server_default="60.0", nullable=True),
        sa.Column("neuro_tags", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("sensory_load", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("avg_engagement", sa.Float(), server_default="0.5", nullable=True),
        sa.Column("use_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("difficulty_level >= 1 AND difficulty_level <= 10", name="knowledge_chunks_difficulty_check"),
        sa.CheckConstraint("sensory_load >= 0 AND sensory_load <= 1", name="knowledge_chunks_sensory_load_check"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("idx_chunks_embedding", "knowledge_chunks", ["embedding"], postgresql_using="ivfflat", postgresql_with={"lists": 256}, postgresql_ops={"embedding": "vector_cosine_ops"})
    op.execute("CREATE INDEX idx_chunks_fts ON knowledge_chunks USING GIN (to_tsvector('english', content))")

    # interactions (hypertable: PK must include partitioning column ts)
    op.create_table(
        "interactions",
        sa.Column("interaction_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_type", sa.String(20), server_default="TEXT", nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.ARRAY(sa.UUID()), nullable=True),
        sa.Column("llm_prompt_hash", sa.String(16), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("engagement_score", sa.Float(), nullable=True),
        sa.Column("child_reaction", sa.String(20), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"]),
        sa.PrimaryKeyConstraint("interaction_id", "ts"),
    )
    op.execute("SELECT create_hypertable('interactions', 'ts', chunk_time_interval => INTERVAL '1 day')")

    # mastery_records
    op.create_table(
        "mastery_records",
        sa.Column("mastery_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("mastery_level", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("stability", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("difficulty", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_due", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("fsrs_state", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["child_profiles.child_id"]),
        sa.PrimaryKeyConstraint("mastery_id"),
        sa.UniqueConstraint("child_id", "topic", name="uq_mastery_child_topic"),
    )
    op.create_index("idx_mastery_due", "mastery_records", ["child_id", "next_review_due"])


def downgrade() -> None:
    op.drop_index("idx_mastery_due", table_name="mastery_records")
    op.drop_table("mastery_records")
    op.execute("SELECT drop_hypertable('interactions', if_exists=True)")
    op.drop_index("idx_chunks_fts", table_name="knowledge_chunks")
    op.drop_index("idx_chunks_embedding", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.execute("SELECT drop_hypertable('behavioral_signals', if_exists=True)")
    op.drop_index("idx_adaptive_state_child", table_name="adaptive_state")
    op.drop_table("adaptive_state")
    op.drop_table("learning_sessions")
    op.drop_table("child_disabilities")
    op.drop_table("neuro_profiles")
    op.drop_table("child_profiles")
    op.drop_table("caregivers")

    op.execute("DROP TYPE signal_type")
    op.execute("DROP TYPE content_format")
    op.execute("DROP TYPE modality_type")
    op.execute("DROP TYPE disability_type")
    op.execute("DROP TYPE diagnosis_type")
