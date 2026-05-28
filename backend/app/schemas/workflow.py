from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import StepType


class WorkflowStepBase(BaseModel):
    name: str = Field(min_length=1)
    type: StepType
    prompt_template: str = Field(min_length=1)
    instructions: str | None = None
    model: str | None = None
    tool_enabled: bool = False


class WorkflowStepCreate(WorkflowStepBase):
    position: int = Field(ge=0)


class WorkflowStepUpdate(WorkflowStepBase):
    id: int | None = None
    position: int = Field(ge=0)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    steps: list[WorkflowStepCreate] = []


class WorkflowUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    steps: list[WorkflowStepUpdate] = []


class WorkflowStepResponse(WorkflowStepBase):
    id: int
    workflow_id: int
    position: int
    created_at: datetime
    updated_at: datetime


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepResponse]


class WorkflowListItem(BaseModel):
    id: int
    name: str
    description: str | None
    step_count: int
    updated_at: datetime
