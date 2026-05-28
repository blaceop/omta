from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.schemas.workflow import WorkflowCreate, WorkflowListItem, WorkflowResponse, WorkflowUpdate
from app.services.workflow_service import create_workflow, delete_workflow, get_workflow, get_workflow_steps, list_workflows, update_workflow
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _serialize_workflow(workflow, steps) -> WorkflowResponse:
    return WorkflowResponse.model_validate(
        {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "steps": [
                {
                    "id": step.id,
                    "workflow_id": step.workflow_id,
                    "position": step.position,
                    "name": step.name,
                    "type": step.type.value,
                    "prompt_template": step.prompt_template,
                    "instructions": step.instructions,
                    "model": step.model,
                    "tool_enabled": step.tool_enabled,
                    "created_at": step.created_at,
                    "updated_at": step.updated_at,
                }
                for step in steps
            ],
        }
    )


@router.get("", response_model=list[WorkflowListItem])
def get_workflows(session: Session = Depends(get_session)) -> list[WorkflowListItem]:
    return list_workflows(session)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def post_workflow(payload: WorkflowCreate, session: Session = Depends(get_session)) -> WorkflowResponse:
    try:
        workflow = create_workflow(session, payload)
        return _serialize_workflow(get_workflow(session, workflow.id), get_workflow_steps(session, workflow.id))
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow_detail(workflow_id: int, session: Session = Depends(get_session)) -> WorkflowResponse:
    try:
        return _serialize_workflow(get_workflow(session, workflow_id), get_workflow_steps(session, workflow_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{workflow_id}", status_code=status.HTTP_200_OK)
def delete_workflow_endpoint(workflow_id: int, session: Session = Depends(get_session)) -> dict:
    try:
        delete_workflow(session, workflow_id)
        return {"deleted": True, "id": workflow_id}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def put_workflow(workflow_id: int, payload: WorkflowUpdate, session: Session = Depends(get_session)) -> WorkflowResponse:
    try:
        workflow = update_workflow(session, workflow_id, payload)
        return _serialize_workflow(workflow, get_workflow_steps(session, workflow.id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
