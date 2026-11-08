#!/usr/bin/env bash
set -e

# Change to the project root directory where langgraph.json lives
cd "$(dirname "$0")"

echo "🚀 Starting local LangGraph server for Coach Clone..."
echo "Running inside the isolated virtual environment (.venv) to avoid global protobuf version mismatches."

if [ -f "./.venv/bin/langgraph" ]; then
    exec ./.venv/bin/langgraph dev --host 127.0.0.1 --port 2024 "$@"
elif command -v uv >/dev/null 2>&1; then
    exec uv run langgraph dev --host 127.0.0.1 --port 2024 "$@"
else
    echo "❌ Error: .venv/bin/langgraph not found and uv is not installed."
    echo "Please run 'uv sync' or set up your virtual environment first."
    exit 1
fi
