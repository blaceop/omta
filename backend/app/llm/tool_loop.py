import json
from typing import Any

from pydantic import BaseModel
from openai import APIConnectionError

from app.llm.client import get_default_model, get_openai_client
from app.schemas.execution import ToolCallTrace
from app.tools.registry import execute_tool, get_tool_definitions
from app.utils.errors import ValidationError


class StepResult(BaseModel):
    output_text: str
    tool_calls: list[ToolCallTrace] = []


async def run_research_with_tools(*, messages: list[dict[str, Any]], model: str | None = None, max_rounds: int = 3) -> StepResult:
    client = get_openai_client()
    selected_model = model or get_default_model()
    tool_defs = get_tool_definitions()
    tool_traces: list[ToolCallTrace] = []
    current_messages = list(messages)

    for _ in range(max_rounds):
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=current_messages,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.input_schema,
                        },
                    }
                    for tool in tool_defs
                ],
                tool_choice="auto",
            )
        except APIConnectionError as exc:
            raise ValidationError(
                "Failed to reach the configured LLM endpoint. Check network connectivity and verify "
                "LLM_API_KEY, LLM_BASE_URL, and LLM_MODEL in backend/.env."
            ) from exc

        message = response.choices[0].message
        if message.tool_calls:
            current_messages.append({"role": "assistant", "content": message.content or "", "tool_calls": message.tool_calls})
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = await execute_tool(tool_call.function.name, args)
                tool_traces.append(
                    ToolCallTrace(tool=tool_call.function.name, arguments=args, result_preview=result[:500])
                )
                current_messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )
            continue

        return StepResult(output_text=message.content or "", tool_calls=tool_traces)

    return StepResult(output_text="Tool loop ended without a final response.", tool_calls=tool_traces)
