"""Deterministic search and agent integration checks; no provider calls."""

import asyncio
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from langchain_core.messages import ToolMessage

from src.agent import get_coach_agent
from src.tools import NO_RESULTS, SEARCH_ERROR, SearchErrorMiddleware, create_search_tool
from tests.test_coach import main


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "TAVILY_API_KEY": "test-tavily-key",
            "OPENROUTER_API_KEY": "test-model-key",
            "LANGSMITH_TRACING": "false",
            "LANGCHAIN_TRACING_V2": "false",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.tool = create_search_tool()
        self.middleware = SearchErrorMiddleware(self.tool.name)
        self.request = SimpleNamespace(tool_call={
            "name": self.tool.name, "id": "search-1", "args": {"query": "exercise technique"},
        })
        self.success = {"results": [{"title": "Example", "url": "https://example.org/evidence", "content": "Evidence"}]}

    def invoke(self):
        return self.tool.invoke({**self.request.tool_call, "type": "tool_call"})

    async def ainvoke(self):
        return await self.tool.ainvoke({**self.request.tool_call, "type": "tool_call"})

    def test_disabled_keys(self):
        for key in ("", " ", "your_tavily_api_key", "YOUR_KEY", "<key>", "placeholder", "example-key"):
            with self.subTest(key=key), patch.dict(os.environ, {"TAVILY_API_KEY": key}):
                self.assertIsNone(create_search_tool())
        with patch.dict(os.environ, clear=True):
            self.assertIsNone(create_search_tool())

    def test_native_configuration(self):
        self.assertEqual(self.tool.name, "tavily_search")
        self.assertIn("query", self.tool.args)
        self.assertEqual(self.tool.max_results, 5)
        self.assertEqual(self.tool.topic, "general")
        self.assertEqual(self.tool.search_depth, "basic")
        self.assertIs(self.tool.include_raw_content, False)
        self.assertIs(self.tool.include_answer, False)
        self.assertIs(self.tool.include_images, False)

    def test_native_results_preserved(self):
        with patch.object(type(self.tool.api_wrapper), "raw_results", return_value=self.success):
            result = self.middleware.wrap_tool_call(self.request, lambda _: self.invoke())
        self.assertEqual(json.loads(result.content), self.success)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.tool_call_id, "search-1")

    def test_empty_results(self):
        with patch.object(type(self.tool.api_wrapper), "raw_results", return_value={"results": []}):
            result = self.middleware.wrap_tool_call(self.request, lambda _: self.invoke())
        self.assertEqual(result.content, NO_RESULTS)
        self.assertEqual(result.status, "error")

    def test_provider_payload_and_raised_errors_are_sanitized(self):
        with patch.object(type(self.tool.api_wrapper), "raw_results", side_effect=RuntimeError("SECRET provider body")):
            result = self.middleware.wrap_tool_call(self.request, lambda _: self.invoke())
        self.assertEqual(result.content, SEARCH_ERROR)
        self.assertNotIn("SECRET", result.content)
        result = self.middleware.wrap_tool_call(self.request, Mock(side_effect=RuntimeError("SECRET")))
        self.assertEqual(result.content, SEARCH_ERROR)
        self.assertEqual(result.status, "error")

    def test_async_success_empty_and_failure(self):
        async def run():
            for payload, expected in ((self.success, None), ({"results": []}, NO_RESULTS)):
                with patch.object(type(self.tool.api_wrapper), "raw_results_async", new=AsyncMock(return_value=payload)):
                    result = await self.middleware.awrap_tool_call(self.request, lambda _: self.ainvoke())
                if expected:
                    self.assertEqual(result.content, expected)
                else:
                    self.assertEqual(json.loads(result.content), self.success)
            with patch.object(type(self.tool.api_wrapper), "raw_results_async", new=AsyncMock(side_effect=RuntimeError("SECRET"))):
                result = await self.middleware.awrap_tool_call(self.request, lambda _: self.ainvoke())
            self.assertEqual(result.content, SEARCH_ERROR)
            result = await self.middleware.awrap_tool_call(self.request, AsyncMock(side_effect=RuntimeError("SECRET")))
            self.assertEqual(result.content, SEARCH_ERROR)
        asyncio.run(run())

    def test_non_search_failures_propagate(self):
        request = SimpleNamespace(tool_call={"name": "read_file", "id": "read-1"})
        with self.assertRaises(RuntimeError):
            self.middleware.wrap_tool_call(request, Mock(side_effect=RuntimeError("unrelated")))
        async def run():
            with self.assertRaises(RuntimeError):
                await self.middleware.awrap_tool_call(request, AsyncMock(side_effect=RuntimeError("unrelated")))
        asyncio.run(run())

    def test_json_and_status_errors_are_sanitized(self):
        for content, status in ((json.dumps({"error": "SECRET"}), "success"), ("SECRET", "error")):
            message = ToolMessage(content=content, tool_call_id="search-1", status=status)
            result = self.middleware.wrap_tool_call(self.request, Mock(return_value=message))
            self.assertEqual(result.content, SEARCH_ERROR)
            self.assertEqual(result.status, "error")

    def test_agent_configuration_and_compilation(self):
        for key in ("", "test-tavily-key"):
            with self.subTest(search=bool(key)), patch.dict(os.environ, {"TAVILY_API_KEY": key}):
                with patch("src.agent.create_deep_agent") as create:
                    get_coach_agent()
                    config = create.call_args.kwargs
                    names = [tool.name for tool in config["tools"]]
                    self.assertEqual(names, ["tavily_search"] if key else [])
                    self.assertEqual(len(config["middleware"]), 1 if key else 0)
                    self.assertNotIn("check_weather", names)
                    self.assertNotIn("online_search", names)
                    if not key:
                        self.assertIn("Internet search is unavailable", config["system_prompt"])
                agent = get_coach_agent()
                self.assertIn("model", agent.get_graph().nodes)

    def test_harness_failure_status(self):
        with patch("builtins.print"), patch("tests.test_coach.get_coach_agent", side_effect=RuntimeError("SECRET")):
            self.assertEqual(main([]), 1)
        with patch("builtins.print"), patch.dict(os.environ, {"TAVILY_API_KEY": ""}):
            self.assertEqual(main(["--live"]), 1)


if __name__ == "__main__":
    unittest.main()
