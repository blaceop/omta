from typing import Any

from pydantic import BaseModel

from app.tools.http_fetch import fetch_url
from app.tools.web_search import search_web


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


def get_tool_definitions() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="web_search",
            description="Search the web for recent information and return the top results with titles, URLs, and snippets.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query."}},
                "required": ["query"],
            },
        ),
        ToolDefinition(
            name="http_fetch",
            description="Fetch the text content of a URL and return a cleaned text preview.",
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The URL to fetch."}},
                "required": ["url"],
            },
        )
    ]


async def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "web_search":
        return await search_web(arguments["query"])
    if name == "http_fetch":
        return await fetch_url(arguments["url"])
    raise ValueError(f"Unsupported tool: {name}")
