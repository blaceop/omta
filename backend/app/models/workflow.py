from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel

from app.utils.timestamps import utcnow


class StepType(str, Enum):
    RESEARCH = "research"
    SUMMARIZE = "summarize"
    DRAFT = "draft"


class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class WorkflowStep(SQLModel, table=True):
    __tablename__ = "workflow_steps"

    id: int | None = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflows.id")
    position: int
    name: str
    type: StepType
    prompt_template: str
    instructions: str | None = None
    model: str | None = None
    tool_enabled: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
