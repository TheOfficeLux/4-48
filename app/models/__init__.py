"""SQLAlchemy ORM models — async, mapped_column."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base for all ORM models."""

    pass


from app.models.caregiver import Caregiver
from app.models.child import ChildDisability, ChildProfile, NeuroProfile
from app.models.session import Interaction, LearningSession
from app.models.knowledge import KnowledgeChunk, MasteryRecord
from app.models.signals import AdaptiveState, BehavioralSignal

__all__ = [
    "Base",
    "Caregiver",
    "ChildProfile",
    "NeuroProfile",
    "ChildDisability",
    "LearningSession",
    "Interaction",
    "KnowledgeChunk",
    "MasteryRecord",
    "BehavioralSignal",
    "AdaptiveState",
]
