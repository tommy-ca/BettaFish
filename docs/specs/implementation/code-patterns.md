# Code Patterns & Standards

## Guiding Principles
- **Deterministic Workflows:** Every DBOS workflow and LangGraph node must be replay-safe with pure functions or idempotent side effects guarded by durable state flags.
- **Explicit State Contracts:** Use TypedDict/Pydantic models for every state mutation to keep migrations predictable.
- **Async by Default:** All I/O (HTTP, DB, file) uses `async` implementations to prevent blocking orchestrators.
- **Observability Everywhere:** Every external interaction emits structured logs, metrics, and traces with shared correlation IDs.

## Directory Layout Expectations
```
src/
├── workflows/        # DBOS workflows & steps
├── graphs/           # LangGraph StateGraph definitions
├── tools/            # Unified tool adapters
├── services/         # Shared services (embeddings, caching)
├── models/           # TypedDict/Pydantic schemas
└── ui/               # Flask + Streamlit interfaces
```

## Workflow Pattern
```python
from dbos import DBOS, step
from typing import TypedDict

class WorkflowState(TypedDict):
    query: str
    selected_agents: list[str]
    agent_results: dict[str, dict]

@DBOS.workflow()
def master_workflow(payload: BettaFishRequest) -> BettaFishResponse:
    state = yield from initialize(payload)
    routing = yield from route_request(state)
    results = yield from execute_agents(routing)
    return yield from finalize(state, results)

@step()
def execute_agents(plan: RoutingDecision) -> dict:
    return WorkflowHandle.map(agent_executor, plan.agents)
```
- Keep workflow files under 300 lines; factor node logic into `services/` or `graphs/` modules.
- Never call blocking libraries within `@step` functions; wrap sync SDKs with `run_in_executor` helpers.

## LangGraph Patterns
- Use `TypedDict` state definitions with `Literal` fields for enumerations.
- Prefer explicit `StateGraph.add_node(name, handler)` and `add_edge` calls; avoid dynamic graph mutation at runtime.
- Encapsulate guardrails as middleware nodes (e.g., `policy_enforcer`) to guarantee consistent compliance checks.
- Always terminate graphs with `END` and register at most one terminal path per SLA category.

## Unified Tool Interface
```python
class TavilySearchTool(BettaFishTool):
    name = "tavily_search"
    max_parallel = 3

    async def execute(self, query: str, *, max_results: int = 5) -> ToolResult:
        request = TavilyPayload(model_dump)
        response = await self._client.search(request)
        return ToolResult.from_tavily(response)
```
- All tools inherit telemetry mixin that records latency, status, and cost tokens.
- Define failure taxonomies (`RateLimitError`, `AuthError`, `UpstreamError`) for consistent retries.

## Configuration Pattern
- All configurable values live in `config/settings.py` using Pydantic `BaseSettings` classes.
- Enforce prefix naming: `BETTAFISH_INSIGHT__OPENAI_API_KEY`, `BETTAFISH_REPORT__TEMPLATE_BUCKET`.
- Support hot-reload by watching `.env` file changes and pushing updates through DBOS config workflow.

## Error Handling
- Raise domain-specific exceptions (e.g., `AgentPlanError`, `ToolExecutionError`).
- Convert to structured error payloads before returning to clients to maintain consistent API contracts.
- Record failures in `agent_results[agent].error` with remediation hints.

## Testing Guidelines
- **Unit Tests:** Target services, tools, and graph node handlers (pytest + anyio).
- **Workflow Tests:** Use DBOS test harness to replay workflows with fixtures.
- **Golden Files:** Store expected report outputs under `tests/golden_reports/` for regression detection.
- **Load Tests:** k6 scenarios for Tavily/Bocha to validate throttling behavior before releases.

## Linting & Formatting
- `ruff` for lint + format enforcement (`ruff format` / `ruff check`).
- `mypy` strict mode to guarantee TypedDict conformance.
- Pre-commit hooks ensure diffs keep docstrings, typing, and localization consistent.

## Acceptance Criteria
- All new modules follow directory layout and linting rules without overrides.
- Workflows replay successfully in CI using deterministic fixtures.
- Tool adapters expose telemetry metadata and typed error classes.
- Config changes hot-reload across agents in <5 s during acceptance tests.
