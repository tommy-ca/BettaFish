# Implementation Plan: Stack A (LangGraph + Hatchet)

## Phase 1: Foundation
- [ ] Install `langgraph`, `hatchet-sdk`.
- [ ] Define `ForumState` schema.

## Phase 2: The Graph
- [ ] Implement `SupervisorNode` (Router).
- [ ] Wrap `QueryEngine` as `QueryAgentNode` (Preserve Tavily tools).
- [ ] Wrap `MindSpider` as `MediaAgentNode` (Expose `run_crawler(platform)` for Weibo, XHS, etc.).
- [ ] Define the `StateGraph` and compile.

## Phase 3: Hatchet Integration
- [ ] Create `hatchet.workflow` to invoke the compiled Graph.
- [ ] Implement Hatchet Workers.
- [ ] **Monitoring**:
    -   Create `watchlist` table.
    -   Implement `monitor_workflow` with diffing logic.

## Phase 4: Data Sources
- [ ] Add Google/Exa tools to `QueryAgentNode`.
- [ ] Add Twitter/YT crawlers to `MediaAgentNode`.
- [ ] **Reporting**: Integrate `ReportEngine` to generate PDF/HTML from the final `ForumState`.
