from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ExecutionStatus, StepType


class ToolCallTrace(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result_preview: str


class ExecutionCreate(BaseModel):
    input_text: str = Field(min_length=1)


class ExecutionStepResponse(BaseModel):
    id: int
    execution_id: int
    workflow_step_id: int
    position: int
    name_snapshot: str
    type_snapshot: StepType
    status: ExecutionStatus
    input_text: str | None
    output_text: str | None
    error_message: str | None
    tool_calls: list[ToolCallTrace] = []
    attempt_count: int
    started_at: datetime | None
    finished_at: datetime | None


class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: ExecutionStatus
    input_text: str
    current_step_position: int | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    steps: list[ExecutionStepResponse]


class ExecutionListItem(BaseModel):
    id: int
    workflow_id: int
    status: ExecutionStatus
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
