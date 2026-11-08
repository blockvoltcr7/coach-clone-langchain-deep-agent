"""Offline compilation smoke check; pass --live to exercise external services."""

import argparse
import os
import re
from unittest.mock import patch

from src.agent import get_coach_agent
from src.tools import create_search_tool


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run paid model/search requests")
    args = parser.parse_args(argv)
    if not args.live:
        try:
            # Compile both configurations without consuming real credentials.
            for search_key in ("", "test-tavily-key"):
                with patch.dict(os.environ, {
                    "OPENROUTER_API_KEY": "test-model-key",
                    "TAVILY_API_KEY": search_key,
                    "LANGSMITH_TRACING": "false",
                    "LANGCHAIN_TRACING_V2": "false",
                }):
                    get_coach_agent()
            print("PASS: Agent compiled with search enabled and disabled. No live queries sent.")
            return 0
        except Exception:
            print("FAIL: Offline agent compilation failed. Run the offline tests for diagnostics.")
            return 1

    if not os.getenv("OPENROUTER_API_KEY") or create_search_tool() is None:
        print("FAIL: --live requires OPENROUTER_API_KEY and a configured TAVILY_API_KEY.")
        return 1

    scenarios = [
        ("Research exercise technique for the Romanian deadlift using internet search. "
         "Cite the supporting source URLs.", "search"),
        ("Use your curated hypertrophy playbook to explain double progression.", "skill"),
    ]
    try:
        agent = get_coach_agent()
        search_name = create_search_tool().name
        for query, kind in scenarios:
            response = agent.invoke({"messages": [("user", query)]}, {"recursion_limit": 100})
            messages = response.get("messages", [])
            calls = [call for msg in messages for call in getattr(msg, "tool_calls", [])]
            final = messages[-1] if messages else None
            content = getattr(final, "content", "")
            if not final or final.type != "ai" or not content or getattr(final, "tool_calls", []):
                raise ValueError("No final answer")
            if any(getattr(msg, "status", None) == "error" for msg in messages):
                raise ValueError("Tool execution failed")
            if kind == "search":
                if not any(call["name"] == search_name for call in calls):
                    raise ValueError("Search was not called")
                if not re.search(r"https?://", str(content)):
                    raise ValueError("Answer lacks source URLs")
            elif not any(
                call["name"] == "read_file" and "hypertrophy_playbook.md" in str(call["args"])
                for call in calls
            ):
                raise ValueError("Curated playbook was not retrieved")
            print(f"PASS: {kind} scenario\n{content}\n")
        return 0
    except Exception:
        # Avoid leaking provider exception bodies or credentials to the terminal.
        print("FAIL: Live verification did not complete successfully (provider, tool, or evidence failure).")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
