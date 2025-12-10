# Gap Analysis: LangGraph Migration

## Analysis Summary
*   **Architectural Shift**: Moving from loose, file-based collaboration (ForumEngine) to strict, state-based graph execution (LangGraph).
*   **Reuse Potential**: Core logic in `InsightEngine` and `MediaEngine` (tools, search, sentiment) is highly reusable but needs refactoring into `Node` classes.
*   **New Infrastructure**: Hatchet and Postgres are critical missing pieces for the "durable execution" requirement.
*   **Missing Integrations**: International sources (Google, Twitter, etc.) are defined in requirements but completely missing in the current codebase (which focuses on Chinese sources).

## Requirement-to-Asset Map

| Requirement | Current Asset | Gap Status | Notes |
| :--- | :--- | :--- | :--- |
| **Intl Data (Google, Twitter)** | `MediaEngine/tools/search.py` | **Missing** | Current search is bespoke or limited. Need new API clients. |
| **Agent Collaboration** | `ForumEngine/monitor.py` | **Constraint** | Current monitor uses Regex on logs. Must be replaced by `StateGraph`. |
| **Durable Execution** | None | **Missing** | No current workflow engine. Hatchet integration is new. |
| **Insight Agent** | `InsightEngine/agent.py` | **Partial** | Logic exists but tied to specific internal DBs. Needs wrapping. |
| **Supervisor Node** | None | **Missing** | No central routing logic exists currently (distributed loop). |

## Implementation Options

### Option A: Hybrid Wrapper (Recommended)
Wrap existing `Engine` classes into LangGraph `Nodes` without rewriting internal logic immediately.
*   **Pros**: Faster time-to-value, reuses tested logic.
*   **Cons**: Keeps some legacy debt (e.g., direct file I/O if not carefully mocked).
*   **Effort**: M (3-7 days)
*   **Risk**: Medium

### Option B: Full Rewrite
Rewrite all agents as native LangGraph components, discarding `Engine` classes.
*   **Pros**: cleanest architecture, full async support.
*   **Cons**: High effort, potential regression of business logic.
*   **Effort**: XL (2+ weeks)
*   **Risk**: High

## Recommendations for Design Phase
1.  **Adopt Option A**: Create adapter classes (e.g., `InsightAgentNode` wraps `InsightEngine`).
2.  **Define State**: rigorously define `ForumState` (TypedDict) to replace unstructured logs.
3.  **Research**: Verify Hatchet's async compatibility with existing synchronous libraries (if any).
