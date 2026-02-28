"""Child profile, neuro profile, and disability ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class DiagnosisType(str, PyEnum):
    ADHD_COMBINED = "ADHD_COMBINED"
    ADHD_INATTENTIVE = "ADHD_INATTENTIVE"
    ADHD_HYPERACTIVE = "ADHD_HYPERACTIVE"
    ASD_L1 = "ASD_L1"
    ASD_L2 = "ASD_L2"
    ASD_L3 = "ASD_L3"
    DYSLEXIA = "DYSLEXIA"
    DYSCALCULIA = "DYSCALCULIA"
    DYSPRAXIA = "DYSPRAXIA"
    ANXIETY = "ANXIETY"
    SPD = "SPD"


class DisabilityType(str, PyEnum):
    VISUAL_IMPAIRMENT = "VISUAL_IMPAIRMENT"
    HEARING_IMPAIRMENT = "HEARING_IMPAIRMENT"
    MOTOR_IMPAIRMENT = "MOTOR_IMPAIRMENT"
    COGNITIVE_DISABILITY = "COGNITIVE_DISABILITY"
    SPEECH_IMPAIRMENT = "SPEECH_IMPAIRMENT"
    CHRONIC_FATIGUE = "CHRONIC_FATIGUE"


class ModalityType(str, PyEnum):
    VISUAL = "VISUAL"
    AUDITORY = "AUDITORY"
    KINESTHETIC = "KINESTHETIC"
    TEXT = "TEXT"
    VIDEO = "VIDEO"
    INTERACTIVE = "INTERACTIVE"


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    caregiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("caregivers.caregiver_id"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    primary_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    grade_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    caregiver: Mapped["Caregiver"] = relationship("Caregiver", back_populates="children")
    neuro_profile: Mapped["NeuroProfile | None"] = relationship(
        "NeuroProfile", back_populates="child", uselist=False, cascade="all, delete-orphan"
    )
    disabilities: Mapped[list["ChildDisability"]] = relationship(
        "ChildDisability", back_populates="child", cascade="all, delete-orphan"
    )


class NeuroProfile(Base):
    __tablename__ = "neuro_profiles"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child_profiles.child_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    diagnoses: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )  # diagnosis_type enum names
    attention_span_mins: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    preferred_modalities: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=lambda: ["TEXT"]
    )
    communication_style: Mapped[str] = mapped_column(String(30), nullable=False, default="LITERAL")
    sensory_thresholds: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=lambda: {"visual": 0.5, "auditory": 0.5, "motion": 0.5}
    )
    ui_preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    hyperfocus_topics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    frustration_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.6)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    child: Mapped["ChildProfile"] = relationship("ChildProfile", back_populates="neuro_profile")


class ChildDisability(Base):
    __tablename__ = "child_disabilities"

    disability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child_profiles.child_id", ondelete="CASCADE"),
        nullable=False,
    )
    disability_type: Mapped[str] = mapped_column(String(50), nullable=False)  # disability_type
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MODERATE")
    accommodations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    child: Mapped["ChildProfile"] = relationship("ChildProfile", back_populates="disabilities")
