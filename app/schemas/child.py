"""Child, neuro profile, and disability schemas."""

from datetime import date
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DiagnosisEnum(str, Enum):
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


class DisabilityType(str, Enum):
    VISUAL_IMPAIRMENT = "VISUAL_IMPAIRMENT"
    HEARING_IMPAIRMENT = "HEARING_IMPAIRMENT"
    MOTOR_IMPAIRMENT = "MOTOR_IMPAIRMENT"
    COGNITIVE_DISABILITY = "COGNITIVE_DISABILITY"
    SPEECH_IMPAIRMENT = "SPEECH_IMPAIRMENT"
    CHRONIC_FATIGUE = "CHRONIC_FATIGUE"


class ChildCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    date_of_birth: date
    primary_language: str = Field(default="en", max_length=10)
    grade_level: str | None = Field(default=None, max_length=10)


class ChildResponse(BaseModel):
    child_id: UUID
    caregiver_id: UUID
    full_name: str
    date_of_birth: date
    primary_language: str
    grade_level: str | None
    created_at: str

    model_config = {"from_attributes": True}


class NeuroprofileUpsertRequest(BaseModel):
    diagnoses: list[DiagnosisEnum] = Field(default_factory=list)
    attention_span_mins: int = Field(ge=1, le=120, default=10)
    preferred_modalities: list[str] = Field(default_factory=lambda: ["TEXT"])
    communication_style: Literal[
        "LITERAL", "NARRATIVE", "VISUAL_FIRST", "GAMIFIED", "SOCRATIC"
    ] = "LITERAL"
    sensory_thresholds: dict[str, float] = Field(
        default_factory=lambda: {"visual": 0.5, "auditory": 0.5, "motion": 0.5}
    )
    ui_preferences: dict = Field(default_factory=dict)
    hyperfocus_topics: list[str] = Field(default_factory=list)
    frustration_threshold: float = Field(default=0.6, ge=0, le=1)


class NeuroprofileResponse(BaseModel):
    profile_id: UUID
    child_id: UUID
    diagnoses: list[str]
    attention_span_mins: int
    preferred_modalities: list[str]
    communication_style: str
    sensory_thresholds: dict
    ui_preferences: dict
    hyperfocus_topics: list[str]
    frustration_threshold: float
    updated_at: str

    model_config = {"from_attributes": True}


class DisabilityAddRequest(BaseModel):
    disability_type: DisabilityType
    severity: Literal["MILD", "MODERATE", "SEVERE"] = "MODERATE"
    accommodations: dict = Field(default_factory=dict)
    notes: str | None = None


class DisabilityResponse(BaseModel):
    disability_id: UUID
    child_id: UUID
    disability_type: str
    severity: str
    accommodations: dict
    notes: str | None
    created_at: str

    model_config = {"from_attributes": True}


class ChildFullResponse(BaseModel):
    child: ChildResponse
    neuro_profile: NeuroprofileResponse | None = None
    disabilities: list[DisabilityResponse] = Field(default_factory=list)
