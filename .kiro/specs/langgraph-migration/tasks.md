# Implementation Tasks

## Phase 1: Foundation (The Graph)
- [ ] 1. Define ForumState and Type Definitions (S)
  - Define `AgentOutput` and `ForumState` TypedDicts in `ForumEngine/graph/state.py`.
  - Implement `merge_research_findings` reducer.
  - Requirement IDs: 2.1, 2.6
- [ ] 2. Implement Wrapper Nodes (Query, Media, Insight) (M) (P)
  - Create `QueryAgentNode` wrapping `QueryEngine`.
  - Create `MediaAgentNode` wrapping `MediaEngine`.
  - Create `InsightAgentNode` wrapping `InsightEngine`.
  - Requirement IDs: 2.2, 2.3, 2.4, 7.1
- [ ] 3. Implement Supervisor Node & Routing Logic (M)
  - Create `SupervisorNode` with LLM-based routing logic.
  - Implement max iteration check and structured JSON output parsing.
  - Requirement IDs: 2.5
- [ ] 4. Construct and Compile StateGraph (S)
  - Assemble nodes and edges in `ForumEngine/graph/graph.py`.
  - Compile graph to runnable app.
  - Requirement IDs: 2.1

## Phase 2: Orchestration (Hatchet)
- [ ] 5. Implement BettaFishWorkflow with Hatchet (M)
  - Create `ForumEngine/graph/workflow.py` with `@hatchet.workflow`.
  - Implement `run_analysis` step invoking the LangGraph app.
  - Requirement IDs: 4.1, 4.2, 5.1
- [ ] 6. Create Worker Entrypoint and Docker Config (S)
  - Create `worker.py` to instantiate Hatchet client and listen for tasks.
  - Requirement IDs: 5.2, 6.2

## Phase 3: Integration & Monitoring
- [ ] 7. Update Flask API to trigger Hatchet Workflows (S)
  - Add `api/v2/analysis` endpoints to `app.py`.
  - Implement POST `/start` and GET `/status/{id}`.
  - Requirement IDs: 7.2, 6.1
- [ ] 8. Implement Watchlist Schema and Cron Workflow (M)
  - Create `watchlist` table in Postgres.
  - Implement `CronWorkflow` in Hatchet to poll watchlist items.
  - Requirement IDs: 3.1, 3.2, 3.3, 3.4, 3.5

## Phase 4: International Data Sources
- [ ] 9. Implement Google Search Tool (S) (P)
  - Create `QueryEngine/tools/google_search.py` using Serper/Google API.
  - Register tool in `QueryAgentNode`.
  - Requirement IDs: 1.1
- [ ] 10. Implement Twitter Scraper Tool (M) (P)
  - Create `MediaEngine/tools/twitter_scraper.py`.
  - Register tool in `MediaAgentNode`.
  - Requirement IDs: 1.2
- [ ] 11. Implement YouTube Transcript Tool (S) (P)
  - Create `MediaEngine/tools/youtube_transcript.py` using `youtube-transcript-api`.
  - Register tool in `MediaAgentNode`.
  - Requirement IDs: 1.2

## Phase 5: Reporting
- [ ] 12. Create Report Adapter for ForumState (S)
  - Implement adapter to convert `ForumState` findings to `ReportEngine` input format.
  - Add `ReportAgentNode` to graph.
  - Requirement IDs: 2.7
