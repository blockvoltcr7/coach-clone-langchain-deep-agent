"""Optional Tavily search and provider-error handling for the coach."""

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langchain_core.tools import ToolException
from langchain_tavily import TavilySearch
from langgraph.types import Command

SEARCH_ERROR = (
    "Internet search is currently unavailable. No research was completed. "
    "Please try again later or check the Tavily configuration."
)
NO_RESULTS = "No search results were found. Try a different query; do not invent sources."


def create_search_tool() -> TavilySearch | None:
    """Return native Tavily search, or None when search is not configured."""
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key or key.lower().startswith(("your_", "your-", "<", "placeholder", "example")):
        return None
    return TavilySearch(
        tavily_api_key=key,
        max_results=5,
        topic="general",
        search_depth="basic",
        include_raw_content=False,
        include_answer=False,
        include_images=False,
        handle_tool_error=False,
    )


ToolResult = ToolMessage | Command[Any]


class SearchErrorMiddleware(AgentMiddleware):
    """Sanitize only search failures, retaining native successful tool results."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    @staticmethod
    def _error(request: ToolCallRequest, content: str = SEARCH_ERROR) -> ToolMessage:
        return ToolMessage(
            content=content,
            tool_call_id=request.tool_call["id"],
            name=request.tool_call["name"],
            status="error",
        )

    def _normalize(self, request: ToolCallRequest, result: ToolResult) -> ToolResult:
        if isinstance(result, ToolMessage):
            # Tavily can return provider exceptions inside an error payload rather
            # than raising them. Never forward those details to the model or UI.
            content = result.content
            if isinstance(content, str):
                try:
                    payload = json.loads(content)
                except (ValueError, TypeError):
                    payload = None
                # Non-JSON exception objects are serialized by BaseTool using
                # Python repr instead. Detect that shape without evaluating it.
                if (isinstance(payload, dict) and "error" in payload) or (
                    payload is None and content.lstrip().startswith(("{'error':", '{"error":'))
                ):
                    return self._error(request)
            if result.status == "error":
                return self._error(request)
        return result

    def wrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolResult]
    ) -> ToolResult:
        if request.tool_call["name"] != self.tool_name:
            return handler(request)
        try:
            return self._normalize(request, handler(request))
        except ToolException as exc:
            message = NO_RESULTS if str(exc).startswith("No search results found") else SEARCH_ERROR
            return self._error(request, message)
        except Exception:
            return self._error(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolResult]],
    ) -> ToolResult:
        if request.tool_call["name"] != self.tool_name:
            return await handler(request)
        try:
            return self._normalize(request, await handler(request))
        except ToolException as exc:
            message = NO_RESULTS if str(exc).startswith("No search results found") else SEARCH_ERROR
            return self._error(request, message)
        except Exception:
            return self._error(request)
