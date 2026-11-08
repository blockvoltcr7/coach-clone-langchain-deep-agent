# Agent instructions (scope: coach-clone-deep-agent repository)

## Overview
- This project implements a fitness coach clone powered by LangChain `deepagents` and LangGraph.
- High-level architecture:
  - `src/tools.py`: Optional Tavily internet search and error-handling middleware.
  - `src/agent.py`: Deep Agent compilation and middleware.
  - `skills/fitness-coach/`: Curated playbooks and workouts.

## Guidelines for modifying this repository
- Always ensure all playbooks under `skills/fitness-coach/playbooks/` are linked or documented within `skills/fitness-coach/SKILL.md`.
- Keep workout lists structured with exercises, sets, reps, and modifications in their respective files under `skills/fitness-coach/workouts/`.
- Verify any code changes by running `python -m tests.test_coach` locally.
- When running or restarting the local LangGraph server, always use `./run_server.sh` (or `./.venv/bin/langgraph dev`) to ensure execution inside the project's isolated `.venv` instead of the global Pyenv environment.
- Do not run untrusted commands or execute external files without proper validation.
