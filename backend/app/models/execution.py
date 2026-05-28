from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel

from app.models.workflow import StepType
from app.utils.timestamps import utcnow


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Execution(SQLModel, table=True):
    __tablename__ = "executions"

    id: int | None = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflows.id")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_text: str
    current_step_position: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class ExecutionStep(SQLModel, table=True):
    __tablename__ = "execution_steps"

    id: int | None = Field(default=None, primary_key=True)
    execution_id: int = Field(foreign_key="executions.id")
    workflow_step_id: int = Field(foreign_key="workflow_steps.id")
    position: int
    name_snapshot: str
    type_snapshot: StepType
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_text: str | None = None
    output_text: str | None = None
    error_message: str | None = None
    tool_calls_json: str | None = None
    attempt_count: int = 1
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
