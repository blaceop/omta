import json

from sqlmodel import Session, select

from app.models.execution import Execution, ExecutionStatus, ExecutionStep
from app.models.workflow import WorkflowStep
from app.schemas.execution import ExecutionCreate
from app.utils.errors import NotFoundError, ValidationError


def create_execution(session: Session, workflow_id: int, payload: ExecutionCreate) -> Execution:
    workflow_steps = session.exec(
        select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id).order_by(WorkflowStep.position)
    ).all()
    if not workflow_steps:
        raise ValidationError("Workflow must contain at least one step before execution.")

    execution = Execution(workflow_id=workflow_id, status=ExecutionStatus.PENDING, input_text=payload.input_text)
    session.add(execution)
    session.flush()

    for step in workflow_steps:
        session.add(
            ExecutionStep(
                execution_id=execution.id,
                workflow_step_id=step.id,
                position=step.position,
                name_snapshot=step.name,
                type_snapshot=step.type,
                status=ExecutionStatus.PENDING,
            )
        )

    session.commit()
    session.refresh(execution)
    return execution


def get_execution(session: Session, execution_id: int) -> Execution:
    execution = session.get(Execution, execution_id)
    if not execution:
        raise NotFoundError(f"Execution {execution_id} not found.")
    return execution


def get_execution_steps(session: Session, execution_id: int) -> list[ExecutionStep]:
    return session.exec(
        select(ExecutionStep).where(ExecutionStep.execution_id == execution_id).order_by(ExecutionStep.position)
    ).all()


def list_workflow_executions(session: Session, workflow_id: int) -> list[Execution]:
    return session.exec(
        select(Execution).where(Execution.workflow_id == workflow_id).order_by(Execution.created_at.desc())
    ).all()


def retry_execution_step(session: Session, execution_id: int, execution_step_id: int) -> Execution:
    execution = get_execution(session, execution_id)
    steps = get_execution_steps(session, execution_id)
    target = next((step for step in steps if step.id == execution_step_id), None)
    if not target:
        raise NotFoundError(f"Execution step {execution_step_id} not found.")
    if target.status != ExecutionStatus.FAILED:
        raise ValidationError("Only failed steps can be retried.")

    for step in steps:
        if step.position >= target.position:
            step.status = ExecutionStatus.PENDING
            step.input_text = None
            step.output_text = None
            step.error_message = None
            step.tool_calls_json = None
            step.started_at = None
            step.finished_at = None
            if step.id == target.id:
                step.attempt_count += 1
            session.add(step)

    execution.status = ExecutionStatus.PENDING
    execution.current_step_position = target.position
    execution.error_message = None
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution
