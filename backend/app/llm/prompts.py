from app.engine.context_builder import StepExecutionContext


def _context_block(context: StepExecutionContext) -> str:
    previous = "\n\n".join(
        f"Step: {item['name']}\nOutput:\n{item['output']}" for item in context.previous_outputs
    ) or "None"
    return (
        f"Original user input:\n{context.original_input}\n\n"
        f"Current step input:\n{context.current_input}\n\n"
        f"Previous completed outputs:\n{previous}"
    )


def build_research_messages(prompt_template: str, instructions: str | None, context: StepExecutionContext) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a research assistant. Prefer using web_search to gather current information. "
                "Use http_fetch only when you already have a promising URL that needs deeper inspection. "
                "If a tool fails, adapt and continue rather than stopping immediately."
            ),
        },
        {
            "role": "user",
            "content": f"{prompt_template}\n\nInstructions:\n{instructions or 'None'}\n\nContext:\n{_context_block(context)}",
        },
    ]


def build_summarize_messages(prompt_template: str, instructions: str | None, context: StepExecutionContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "You summarize information clearly and concisely."},
        {
            "role": "user",
            "content": f"{prompt_template}\n\nInstructions:\n{instructions or 'None'}\n\nContext:\n{_context_block(context)}",
        },
    ]


def build_draft_messages(prompt_template: str, instructions: str | None, context: StepExecutionContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "You draft polished, useful content from prior context."},
        {
            "role": "user",
            "content": f"{prompt_template}\n\nInstructions:\n{instructions or 'None'}\n\nContext:\n{_context_block(context)}",
        },
    ]
