# Implementation Plan: Stack A (LangGraph + Hatchet)

This plan details the steps to modernize the BettaFish system by replacing the legacy log-based forum with a LangGraph state machine and Hatchet durable execution.

## Phase 1: Foundation (The Graph)
**Goal**: Establish the `ForumState`, the core graph topology, and the Supervisor Node.

- [ ] **State Definition**:
    - [ ] Create `ForumEngine/graph/state.py`.
    - [ ] Define `AgentOutput` (TypedDict) with fields: `agent_name`, `summary`, `data`, `artifacts`.
    - [ ] Define `ForumState` (TypedDict) with fields: `messages`, `research_findings` (merged), `user_query`, `iteration_count`, `next_speaker`, `session_id`.
    - [ ] Implement `merge_research_findings` reducer function.

- [ ] **Agent Wrappers (Nodes)**:
    - [ ] Create `ForumEngine/graph/nodes/query_agent.py`.
        - [ ] Implement `QueryAgentNode` class inheriting from a base `GraphNode`.
        - [ ] Adapts `QueryEngine/agent.py`: Receives state, calls `DeepSearchAgent` logic (synchronously for now), returns `AgentOutput`.
    - [ ] Create `ForumEngine/graph/nodes/media_agent.py`.
        - [ ] Implement `MediaAgentNode`.
        - [ ] Adapts `MindSpider` logic: Triggers crawling/sentiment analysis, returns `AgentOutput`.
    - [ ] Create `ForumEngine/graph/nodes/insight_agent.py`.
        - [ ] Implement `InsightAgentNode`.
        - [ ] Adapts `InsightEngine` logic: Queries internal DB, returns `AgentOutput`.

- [ ] **Supervisor Node (Router)**:
    - [ ] Create `ForumEngine/graph/nodes/supervisor.py`.
    - [ ] Implement logic to analyze `ForumState.messages`.
    - [ ] Use a structured LLM call (JSON mode) to decide:
        - `next_speaker`: one of `["QueryAgent", "MediaAgent", "InsightAgent", "ReportAgent"]`.
        - `reasoning`: string explaining the choice.
    - [ ] Enforce `MAX_ITERATIONS` logic to prevent infinite loops (default 5).

- [ ] **Graph Construction**:
    - [ ] Create `ForumEngine/graph/graph.py`.
    - [ ] Initialize `StateGraph(ForumState)`.
    - [ ] Add nodes: `supervisor`, `query_agent`, `media_agent`, `insight_agent`.
    - [ ] Define conditional edges from `supervisor` based on `next_speaker`.
    - [ ] Define edges from agents back to `supervisor`.
    - [ ] Compile the graph into a `CompiledGraph` runnable.

## Phase 2: Orchestration (Hatchet)
**Goal**: Wrap the LangGraph execution in a durable Hatchet workflow.

- [ ] **Dependencies**:
    - [ ] Ensure `hatchet-sdk` is installed (already in requirements.txt).
    - [ ] Set up a local Hatchet instance (Docker) or use Hatchet Cloud for dev.

- [ ] **Worker Implementation**:
    - [ ] Create `ForumEngine/graph/workflow.py`.
    - [ ] Define `BettaFishWorkflow` class decorated with `@hatchet.workflow`.
    - [ ] Implement `run_analysis` step:
        - [ ] Input: `{ "query": str }`.
        - [ ] Initialize `ForumState`.
        - [ ] `await graph.ainvoke(initial_state)`.
        - [ ] Return final state.

- [ ] **Worker Entrypoint**:
    - [ ] Create `worker.py` in root (or `ForumEngine/worker.py`).
    - [ ] Instantiate `Hatchet` client.
    - [ ] Register `BettaFishWorkflow`.
    - [ ] Start worker loop.

## Phase 3: Integration & Monitoring
**Goal**: Connect the new system to the outside world and the existing Flask app.

- [ ] **API Endpoint**:
    - [ ] Update `app.py` or add a new blueprint `api/v2/analysis`.
    - [ ] POST `/start`: Triggers `hatchet.admin.run_workflow("BettaFishWorkflow", input=...)`.
    - [ ] GET `/status/{run_id}`: Proxies Hatchet API to get run status.

- [ ] **Watchlist (Active Monitoring)**:
    - [ ] Define Postgres schema for `watchlist` table (id, query, schedule, last_result_hash).
    - [ ] Create a `CronWorkflow` in Hatchet.
    - [ ] Logic: Fetch active items -> Spawn `BettaFishWorkflow` -> Diff result -> Notify if significant.

## Phase 4: Expansion (Data Sources)
**Goal**: Add the new international data sources required by `MR-01`.

- [ ] **Google Search Tool**:
    - [ ] Implement `QueryEngine/tools/google_search.py` (using Serper or Google API).
    - [ ] Register tool in `QueryAgentNode`.

- [ ] **Twitter/X Scraper**:
    - [ ] Implement `MediaEngine/tools/twitter_scraper.py` (using Playwright/social-data-api).
    - [ ] Register tool in `MediaAgentNode`.

- [ ] **YouTube Transcript**:
    - [ ] Implement `MediaEngine/tools/youtube_transcript.py`.
    - [ ] Register tool in `MediaAgentNode`.

## Phase 5: Reporting
**Goal**: Ensure the legacy ReportEngine can consume the new `ForumState`.

- [ ] **Report Adapter**:
    - [ ] Create an adapter that converts `ForumState.research_findings` into the file structure expected by `ReportEngine` (or refactor `ReportEngine` to accept state objects).
    - [ ] Add `ReportAgentNode` to the graph as the final step.