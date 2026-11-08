# Application diagrams

Three complementary views explain the current Coach Clone implementation. PNG images render directly in the root README; SVG files provide vector versions. Download the standalone HTML files and open them in a browser for interactive exploration, theme switching, and exports.

| Diagram | What it explains | Interactive version | Editable definition |
| --- | --- | --- | --- |
| System architecture | UI → LangGraph → coach runtime, model, skills, optional search, and artifacts | [HTML](system-architecture.html) | [Archify JSON](sources/system-architecture.json) |
| Research workflow | Model-directed coaching/research, optional search, results, and failure paths | [HTML](research-workflow.html) | [Archify JSON](sources/research-workflow.json) |
| Knowledge and state | Browser settings, streamed graph values, coaching files, and physical artifacts | [HTML](knowledge-and-state.html) | [Archify JSON](sources/knowledge-and-state.json) |

## Reading the diagrams

- Connections summarize interactions; they are not an exhaustive network trace or a literal compiled graph.
- Search is registered at startup only when a non-placeholder Tavily key is configured. A configured but invalid key still registers the tool and can fail at execution time.
- Workout retrieval, search selection, and citations are model-directed behaviors specified by the prompt. The agent can combine retrieval and research in one request and use multiple tool steps.
- The workflow's disabled-search branch is an instruction to explain missing configuration. It does not pass through search middleware, because no search tool is registered.
- Files/storage symbols represent local files or browser storage, not SQL databases. Graph state is framework-managed; no external database deployment or durability guarantee is implied.
- `state.files` and physical `workspace/` artifacts are distinct. No synchronization bridge is implemented.
- The workspace is shared, and `virtual_mode=False` is not a filesystem sandbox.
- Framework planning and subagent capabilities are grouped inside the coach runtime. Generic approval/debug controls in the UI do not establish a mandatory backend approval gate.
- Optional tracing, development internals, deployment topology, and performance timings are outside these diagrams.

## Source evidence

The supplied project folder has no Git metadata. These maps describe inspected working-tree files rather than a pinned commit. Archify's layout and browser checks validate the diagrams, not committed source provenance or application correctness.

The [source manifest](sources/source-evidence.json) records repository-relative paths, inspected line ranges, SHA-256 hashes, and coverage by diagram. It contains no credentials, conversation data, or environment-file values.

Key implementation references:

- [Agent assembly and instructions](../../src/agent.py)
- [Search configuration and error middleware](../../src/tools.py)
- [OpenRouter configuration](../../src/config.py)
- [Graph registration](../../langgraph.json)
- [Chat streaming and file-state operations](../../deep-agents-ui/src/app/hooks/useChat.ts)
- [Browser configuration persistence](../../deep-agents-ui/src/lib/config.ts)
- [Coaching skill and content index](../../skills/fitness-coach/SKILL.md)

## Regeneration

Use the Archify skill's CLI with Node.js and a supported Chrome/Chromium browser. Set `ARCHIFY_CLI` to the absolute path of its installed `bin/archify.mjs` file, then run from the project root:

```bash
node "$ARCHIFY_CLI" finalize architecture docs/diagrams/sources/system-architecture.json docs/diagrams/system-architecture.html --quality showcase --out-dir .archify/system-review-next --json
node "$ARCHIFY_CLI" finalize workflow docs/diagrams/sources/research-workflow.json docs/diagrams/research-workflow.html --quality showcase --out-dir .archify/research-review-next --json
node "$ARCHIFY_CLI" finalize architecture docs/diagrams/sources/knowledge-and-state.json docs/diagrams/knowledge-and-state.html --quality showcase --out-dir .archify/state-review-next --json
```

Choose a fresh review directory after each candidate change. In each delivered HTML viewer, select the light theme and use **Export → PNG** and **Export → SVG · Light**. Save the exports with the corresponding diagram stem, then review the images at README width. Refresh the source manifest whenever the implementation changes.

Local validation receipts and scratch authoring files are ignored by Git; the shareable HTML, images, editable definitions, and source manifest remain included.
