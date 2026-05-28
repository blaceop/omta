from pydantic import BaseModel
from sqlmodel import Session, select

from app.models.execution import Execution, ExecutionStep, ExecutionStatus


class StepExecutionContext(BaseModel):
    original_input: str
    previous_outputs: list[dict[str, str]]
    current_input: str
    attempt_count: int = 1


def build_step_context(
    session: Session,
    execution: Execution,
    current_position: int,
    attempt_count: int = 1,
) -> StepExecutionContext:
    previous_steps = session.exec(
        select(ExecutionStep)
        .where(ExecutionStep.execution_id == execution.id)
        .where(ExecutionStep.position < current_position)
        .order_by(ExecutionStep.position)
    ).all()

    previous_outputs = [
        {"name": step.name_snapshot, "output": step.output_text or ""}
        for step in previous_steps
        if step.status == ExecutionStatus.SUCCEEDED
    ]
    current_input = execution.input_text if current_position == 0 else (previous_outputs[-1]["output"] if previous_outputs else "")

    return StepExecutionContext(
        original_input=execution.input_text,
        previous_outputs=previous_outputs,
        current_input=current_input,
        attempt_count=attempt_count,
    )
