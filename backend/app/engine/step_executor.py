from app.engine.context_builder import StepExecutionContext
from app.llm.client import get_default_model, get_openai_client
from app.llm.prompts import build_draft_messages, build_research_messages, build_summarize_messages
from app.llm.tool_loop import StepResult, run_research_with_tools
from app.models.workflow import StepType, WorkflowStep


async def _run_plain_llm(messages: list[dict[str, str]], model: str | None) -> StepResult:
    client = get_openai_client()
    response = client.chat.completions.create(model=model or get_default_model(), messages=messages)
    return StepResult(output_text=response.choices[0].message.content or "")


def _should_fail_once(workflow_step: WorkflowStep, context: StepExecutionContext) -> bool:
    instructions = (workflow_step.instructions or "").lower()
    return "[demo_fail_once]" in instructions and context.attempt_count == 1


async def execute_workflow_step(workflow_step: WorkflowStep, context: StepExecutionContext) -> StepResult:
    if _should_fail_once(workflow_step, context):
        raise RuntimeError(
            "Demo retry trigger: this step intentionally fails on the first attempt. Click Retry Step to continue."
        )

    if workflow_step.type == StepType.RESEARCH:
        messages = build_research_messages(workflow_step.prompt_template, workflow_step.instructions, context)
        return await run_research_with_tools(messages=messages, model=workflow_step.model)
    if workflow_step.type == StepType.SUMMARIZE:
        messages = build_summarize_messages(workflow_step.prompt_template, workflow_step.instructions, context)
        return await _run_plain_llm(messages, workflow_step.model)
    if workflow_step.type == StepType.DRAFT:
        messages = build_draft_messages(workflow_step.prompt_template, workflow_step.instructions, context)
        return await _run_plain_llm(messages, workflow_step.model)
    raise ValueError(f"Unsupported step type: {workflow_step.type}")
