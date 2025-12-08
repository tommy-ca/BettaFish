# Architecture Design: Stack A (LangGraph + Hatchet)

## 1. Core Concept: "The Forum as a Graph"

We are transitioning from a file-based log monitoring system to a structured **StateGraph** orchestrated by **LangGraph** and executed durably by **Hatchet**.

### 1.1 The "Forum" Metaphor
In the legacy system, the "Forum" was a log file where agents dumped text. In the new system, the "Forum" is a shared `State` object passed between Nodes (Agents).
*   **The Host (Supervisor)**: A routing node that decides which agent speaks next or if the discussion is over.
*   **The Agents**: Specialized nodes (Query, Media, Insight) that receive the current state, perform work, and return a state update.
*   **The Minutes (State)**: A structured record of all findings, messages, and reports.

## 2. Shared State Architecture

The `ForumState` serves as the single source of truth for the collaboration.

```python
from typing import TypedDict, List, Dict, Any, Annotated, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentOutput(TypedDict):
    """Structured output from a specific agent's turn."""
    agent_name: str
    summary: str             # High-level summary of findings
    data: Dict[str, Any]     # Raw structured data (e.g., search results, crawl stats)
    artifacts: List[str]     # Paths to generated files (images, PDFs)

class ForumState(TypedDict):
    # --- Conversation History ---
    # The linear history of the "debate" for the LLM Supervisor to read.
    messages: Annotated[List[BaseMessage], operator.add]
    
    # --- Structured Knowledge Base ---
    # Aggregated findings from each engine, keyed by engine name or topic.
    # Replaces the need to parse regex from logs.
    research_findings: Annotated[Dict[str, List[AgentOutput]], operator.add]
    
    # --- Control Flow ---
    user_query: str          # The original objective
    iteration_count: int     # To prevent infinite loops (Supervisor triggers exit after N rounds)
    next_speaker: str        # Set by Supervisor to route to specific node
    
    # --- Metadata ---
    session_id: str
    timestamp: str
```

## 3. Graph Topology & Nodes

### 3.1 Supervisor Node (Router)
*   **Input**: `ForumState` (specifically `messages` and `user_query`).
*   **Logic**:
    1.  Analyzes the conversation so far.
    2.  Determines if sufficient information has been gathered.
    3.  **Routing**:
        *   If `iteration_count` > MAX_ROUNDS -> `ReportEngine`.
        *   If information gap exists -> Selects `QueryAgentNode`, `MediaAgentNode`, or `InsightAgentNode`.
        *   If consensus reached -> `ReportEngine`.
*   **Output**: Updates `next_speaker`.

### 3.2 Agent Nodes (Wrappers)
These nodes wrap the existing logic of the Engines, adapting them to the Graph interface.

*   **`QueryAgentNode`**:
    *   **Wraps**: `QueryEngine/agent.py`
    *   **Action**: Receives the query/context. Calls `TavilyNewsAgency` or new Google tools. Generates a summary.
    *   **Returns**: `AgentOutput` with `agent_name="QueryEngine"`.

*   **`MediaAgentNode`**:
    *   **Wraps**: `MindSpider` functionality.
    *   **Action**:
        *   Extracts topics/keywords from `messages`.
        *   Triggers `MindSpider` crawlers (Weibo, XHS, etc.) either directly or via Hatchet child-workflows.
        *   Analyzes sentiment.
    *   **Returns**: `AgentOutput` with `agent_name="MediaEngine"` and crawled data stats.

*   **`InsightAgentNode`**:
    *   **Wraps**: `InsightEngine` (Private DB mining).
    *   **Action**: Queries internal SQL databases for historical context.
    *   **Returns**: `AgentOutput` with `agent_name="InsightEngine"`.

### 3.3 Report Node (Exit)
*   **Wraps**: `ReportEngine`.
*   **Action**:
    *   Reads `research_findings` and `messages`.
    *   Selects template.
    *   Generates HTML/PDF.
*   **Output**: `END` (Graph termination).

### 3.4 Graph Definition (Pseudocode)
```python
workflow = StateGraph(ForumState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("query_agent", query_agent_node)
workflow.add_node("media_agent", media_agent_node)
workflow.add_node("insight_agent", insight_agent_node)
workflow.add_node("report_agent", report_agent_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_speaker"],
    {
        "QueryEngine": "query_agent",
        "MediaEngine": "media_agent",
        "InsightEngine": "insight_agent",
        "ReportEngine": "report_agent",
        "FINISH": END
    }
)

# Agents return to Supervisor
workflow.add_edge("query_agent", "supervisor")
workflow.add_edge("media_agent", "supervisor")
workflow.add_edge("insight_agent", "supervisor")
workflow.add_edge("report_agent", END)
```

## 4. Orchestration with Hatchet

Hatchet provides the durable execution layer. We don't just run the graph in memory; we define a Hatchet Workflow that *invokes* the graph.

### 4.1 Workflow Definition
```python
@hatchet.workflow(name="bettafish-analysis-workflow")
class BettaFishWorkflow:
    @hatchet.step()
    async def run_analysis(self, context):
        # Initialize State
        initial_state = ForumState(
            user_query=context.input("query"),
            messages=[],
            research_findings={},
            iteration_count=0
        )
        
        # Run LangGraph
        # We can run the entire graph as one step, OR break nodes into Hatchet steps
        # For Phase 1, we run the graph as a compiled runnable.
        app = workflow.compile()
        final_state = await app.ainvoke(initial_state)
        
        return final_state
```

### 4.2 Watchlist & Monitoring
To support the "Active Monitoring" requirement:

1.  **Watchlist Table**: Stores queries/topics and a hash of the last known result.
2.  **Cron Workflow**: A separate Hatchet workflow running e.g., every hour.
    *   Fetches active items from Watchlist.
    *   Spawns `bettafish-analysis-workflow` for each.
    *   **Smart Diff**: The `SupervisorNode` can be primed with `last_snapshot` to decide if "Nothing new found" and exit early.

## 5. Directory Structure Changes

We will introduce a new module structure within `ForumEngine` to house this logic, gradually deprecating the file-monitoring code.

```
ForumEngine/
├── __init__.py
├── monitor.py          # (Legacy) Log file monitor
├── llm_host.py         # (Legacy) LLM Host logic
├── graph/              # (New) Graph implementation
│   ├── __init__.py
│   ├── state.py        # ForumState definition
│   ├── graph.py        # StateGraph construction and compilation
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── supervisor.py
│   │   ├── query_agent.py
│   │   ├── media_agent.py
│   │   └── insight_agent.py
│   └── workflow.py     # Hatchet workflow entrypoint
```

## 6. Migration Strategy

1.  **Parallel Run**: We can run the new Graph-based `ForumEngine` alongside the old file-based one during development.
2.  **Tool Reuse**: The new Nodes will import the *Tool* classes (e.g., `TavilyNewsAgency`) from the existing Engine directories, ensuring logic reuse.
3.  **Cutover**: Once the Graph is stable, we switch the `app.py` `/api/search` endpoint to trigger the Hatchet workflow instead of spawning subprocesses.