import asyncio
import json

from sqlmodel import Session, select

from app.config import get_settings
from app.db import engine
from app.engine.context_builder import build_step_context
from app.engine.step_executor import execute_workflow_step
from app.models.execution import Execution, ExecutionStatus, ExecutionStep
from app.models.workflow import WorkflowStep
from app.utils.timestamps import utcnow

settings = get_settings()


async def run_execution(execution_id: int) -> None:
    await resume_execution_from_step(execution_id, 0)


async def resume_execution_from_step(execution_id: int, start_position: int) -> None:
    with Session(engine) as session:
        execution = session.get(Execution, execution_id)
        if not execution:
            return

        execution.status = ExecutionStatus.RUNNING
        execution.started_at = execution.started_at or utcnow()
        execution.error_message = None
        session.add(execution)
        session.commit()

    with Session(engine) as session:
        execution = session.get(Execution, execution_id)
        steps = session.exec(
            select(ExecutionStep).where(ExecutionStep.execution_id == execution_id).order_by(ExecutionStep.position)
        ).all()

        for step in steps:
            if step.position < start_position or step.status == ExecutionStatus.SUCCEEDED:
                continue

            workflow_step = session.get(WorkflowStep, step.workflow_step_id)
            execution.current_step_position = step.position
            step.status = ExecutionStatus.RUNNING
            step.started_at = utcnow()
            context = build_step_context(session, execution, step.position, step.attempt_count)
            step.input_text = context.current_input
            session.add(execution)
            session.add(step)
            session.commit()

            if settings.execution_step_transition_delay_ms > 0:
                await asyncio.sleep(settings.execution_step_transition_delay_ms / 1000)

            try:
                result = await execute_workflow_step(workflow_step, context)
                step.output_text = result.output_text
                step.tool_calls_json = json.dumps([trace.model_dump() for trace in result.tool_calls])
                step.status = ExecutionStatus.SUCCEEDED
                step.finished_at = utcnow()
                session.add(step)
                session.commit()
            except Exception as exc:  # noqa: BLE001
                step.error_message = str(exc)
                step.status = ExecutionStatus.FAILED
                step.finished_at = utcnow()
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(exc)
                execution.finished_at = utcnow()
                session.add(step)
                session.add(execution)
                session.commit()
                return

        execution.status = ExecutionStatus.SUCCEEDED
        execution.finished_at = utcnow()
        execution.current_step_position = None
        session.add(execution)
        session.commit()
