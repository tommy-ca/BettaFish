# Technical Design Discovery Log

## Summary
The discovery phase focused on analyzing the existing architectural plans for the LangGraph and Hatchet migration. The project already has detailed architecture and implementation plans (`docs/specs/architecture_design_langgraph.md` and `implementation_plan_langgraph.md`). The key challenge is safely migrating from a file-based legacy system to a strongly-typed, durable execution model without breaking existing business logic. The `ForumState` will be the central source of truth, replacing log files.

## Research Topics

### LangGraph Integration
- **Source**: `docs/specs/architecture_design_langgraph.md`
- **Finding**: LangGraph `StateGraph` will orchestrate the conversation.
- **Implication**: Need to define a strict `ForumState` (TypedDict) that holds messages, findings, and metadata. Agents will be wrapped in Nodes.

### Hatchet Orchestration
- **Source**: `docs/specs/architecture_design_langgraph.md`
- **Finding**: Hatchet will wrap the entire LangGraph execution as a durable workflow step.
- **Implication**: Need a `BettaFishWorkflow` class in `ForumEngine/graph/workflow.py`. Hatchet handles retries and cron scheduling for monitoring.

### Legacy Agent Wrapping
- **Source**: `docs/specs/implementation_plan_langgraph.md`
- **Finding**: Existing `Engine` classes (Query, Media, Insight) contain valuable logic and tools.
- **Implication**: We should not rewrite them initially. Instead, create `Node` classes (e.g., `QueryAgentNode`) that import and invoke the existing agent logic, acting as adapters.

### International Data Sources
- **Source**: `docs/specs/requirements.md`
- **Finding**: Requirements mandate Google, Twitter, YouTube support.
- **Implication**: These are missing from the codebase and must be implemented as new Tools in Phase 4 of the implementation plan.

## Architecture Decisions

### Orchestration Pattern
- **Context**: Moving away from file-based `monitor.py`.
- **Options Evaluated**:
  1. **LangGraph + Hatchet (Selected)** - Defined in steering specs.
  2. **Claude Agent SDK** - Rejected in favor of LangGraph's explicit control.
- **Decision**: LangGraph for internal agent loops, Hatchet for external durability.
- **Rationale**: Steering documents explicitly select this stack (Stack A).

### State Management
- **Context**: How agents share data.
- **Decision**: Single shared `ForumState` TypedDict.
- **Rationale**: Provides type safety and a single source of truth, replacing unstructured logs.

### Legacy Integration
- **Context**: How to use existing code.
- **Decision**: Adapter Pattern (Wrapper Nodes).
- **Rationale**: Reduces risk and effort by reusing tested logic (Search, Sentiment) while modernizing the control flow.

## Risks & Open Questions
- **Risk 1**: Async/Sync friction. Hatchet and LangGraph are async-native, but legacy code is likely synchronous.
- **Mitigation**: Run legacy code in threadpools or ensure wrappers are async-friendly.
- **Question 1**: Is the ReportEngine adaptable to a dict-based state instead of files?
- **Status**: Needs investigation in Phase 5. Adapter planned.
