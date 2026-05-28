import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.engine.runner import resume_execution_from_step, run_execution
from app.schemas.execution import ExecutionCreate, ExecutionListItem, ExecutionResponse
from app.services.execution_service import (
    create_execution,
    get_execution,
    get_execution_steps,
    list_workflow_executions,
    retry_execution_step,
)
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter(tags=["executions"])


def _serialize_execution(execution, steps) -> ExecutionResponse:
    return ExecutionResponse.model_validate(
        {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "input_text": execution.input_text,
            "current_step_position": execution.current_step_position,
            "error_message": execution.error_message,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "created_at": execution.created_at,
            "steps": [
                {
                    "id": step.id,
                    "execution_id": step.execution_id,
                    "workflow_step_id": step.workflow_step_id,
                    "position": step.position,
                    "name_snapshot": step.name_snapshot,
                    "type_snapshot": step.type_snapshot.value,
                    "status": step.status.value,
                    "input_text": step.input_text,
                    "output_text": step.output_text,
                    "error_message": step.error_message,
                    "tool_calls": json.loads(step.tool_calls_json) if step.tool_calls_json else [],
                    "attempt_count": step.attempt_count,
                    "started_at": step.started_at,
                    "finished_at": step.finished_at,
                }
                for step in steps
            ],
        }
    )


@router.post("/api/workflows/{workflow_id}/executions", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def post_execution(
    workflow_id: int,
    payload: ExecutionCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> ExecutionResponse:
    try:
        execution = create_execution(session, workflow_id, payload)
        background_tasks.add_task(run_execution, execution.id)
        execution = get_execution(session, execution.id)
        return _serialize_execution(execution, get_execution_steps(session, execution.id))
    except (NotFoundError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/workflows/{workflow_id}/executions", response_model=list[ExecutionListItem])
def get_workflow_execution_list(workflow_id: int, session: Session = Depends(get_session)) -> list[ExecutionListItem]:
    executions = list_workflow_executions(session, workflow_id)
    return [
        ExecutionListItem(
            id=item.id,
            workflow_id=item.workflow_id,
            status=item.status.value,
            started_at=item.started_at,
            finished_at=item.finished_at,
            created_at=item.created_at,
        )
        for item in executions
    ]


@router.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution_detail(execution_id: int, session: Session = Depends(get_session)) -> ExecutionResponse:
    try:
        return _serialize_execution(get_execution(session, execution_id), get_execution_steps(session, execution_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/executions/{execution_id}/steps/{execution_step_id}/retry", response_model=ExecutionResponse)
def post_retry_execution_step(
    execution_id: int,
    execution_step_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> ExecutionResponse:
    try:
        execution = retry_execution_step(session, execution_id, execution_step_id)
        background_tasks.add_task(resume_execution_from_step, execution.id, execution.current_step_position or 0)
        execution = get_execution(session, execution.id)
        return _serialize_execution(execution, get_execution_steps(session, execution.id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
