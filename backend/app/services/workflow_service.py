from sqlmodel import Session, select

from app.models.execution import Execution, ExecutionStep
from app.models.workflow import StepType as ModelStepType
from app.models.workflow import Workflow, WorkflowStep
from app.schemas.workflow import WorkflowCreate, WorkflowListItem, WorkflowUpdate
from app.utils.errors import NotFoundError, ValidationError
from app.utils.timestamps import utcnow


def _validate_positions(steps: list) -> None:
    positions = sorted(step.position for step in steps)
    if positions != list(range(len(steps))):
        raise ValidationError("Step positions must be unique and continuous starting at 0.")


def _to_model_step_type(value: str) -> ModelStepType:
    return ModelStepType(value)


def list_workflows(session: Session) -> list[WorkflowListItem]:
    workflows = session.exec(select(Workflow)).all()
    items: list[WorkflowListItem] = []
    for workflow in workflows:
        steps = session.exec(select(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id)).all()
        items.append(
            WorkflowListItem(
                id=workflow.id,
                name=workflow.name,
                description=workflow.description,
                step_count=len(steps),
                updated_at=workflow.updated_at,
            )
        )
    return items


def create_workflow(session: Session, payload: WorkflowCreate) -> Workflow:
    _validate_positions(payload.steps)
    workflow = Workflow(name=payload.name, description=payload.description)
    session.add(workflow)
    session.flush()

    for step in payload.steps:
        workflow_step = WorkflowStep(
            workflow_id=workflow.id,
            position=step.position,
            name=step.name,
            type=_to_model_step_type(step.type.value),
            prompt_template=step.prompt_template,
            instructions=step.instructions,
            model=step.model,
            tool_enabled=step.tool_enabled,
        )
        session.add(workflow_step)

    session.commit()
    session.refresh(workflow)
    return workflow


def get_workflow_steps(session: Session, workflow_id: int) -> list[WorkflowStep]:
    return session.exec(
        select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id).order_by(WorkflowStep.position)
    ).all()


def get_workflow(session: Session, workflow_id: int) -> Workflow:
    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        raise NotFoundError(f"Workflow {workflow_id} not found.")
    return workflow


def delete_workflow(session: Session, workflow_id: int) -> None:
    workflow = get_workflow(session, workflow_id)

    # Delete execution steps then executions first (FK order)
    executions = session.exec(select(Execution).where(Execution.workflow_id == workflow_id)).all()
    for execution in executions:
        exec_steps = session.exec(
            select(ExecutionStep).where(ExecutionStep.execution_id == execution.id)
        ).all()
        for exec_step in exec_steps:
            session.delete(exec_step)
        session.delete(execution)
    session.flush()

    # Delete workflow steps
    wf_steps = session.exec(select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)).all()
    for step in wf_steps:
        session.delete(step)
    session.flush()

    session.delete(workflow)
    session.commit()


def update_workflow(session: Session, workflow_id: int, payload: WorkflowUpdate) -> Workflow:
    _validate_positions(payload.steps)
    workflow = get_workflow(session, workflow_id)
    workflow.name = payload.name
    workflow.description = payload.description
    workflow.updated_at = utcnow()
    session.add(workflow)

    existing_steps = session.exec(select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)).all()
    for step in existing_steps:
        session.delete(step)
    session.flush()

    for step in payload.steps:
        workflow_step = WorkflowStep(
            workflow_id=workflow.id,
            position=step.position,
            name=step.name,
            type=_to_model_step_type(step.type.value),
            prompt_template=step.prompt_template,
            instructions=step.instructions,
            model=step.model,
            tool_enabled=step.tool_enabled,
        )
        session.add(workflow_step)

    session.commit()
    session.refresh(workflow)
    return workflow
