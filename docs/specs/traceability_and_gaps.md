# Traceability & Gaps – BettaFish

This document maps high-level requirements to their implementing components and records known gaps or open questions. It covers both the **Legacy (Current)** system and the **Modernization (Planned)** architecture.

---

## 1. Legacy Requirement Traceability (FR-xx)

This table summarizes where key legacy requirements are primarily implemented.

- **FR-01 – End-to-End Analysis Workflow**  
  - Main components: `app.py`, `QueryEngine/agent.py`, `MediaEngine/agent.py`, `InsightEngine/agent.py`, `ForumEngine/monitor.py`, `ReportEngine/agent.py`.

- **FR-02 – Configurable Environment & Credentials**  
  - `config.py`, `app.py` (`/api/config`).

- **FR-03 – Docker & Source Deployments**  
  - `docker-compose.yml`, `Dockerfile`.

- **FR-10/11 – QueryEngine Search & Reflection**  
  - `QueryEngine/agent.py`, `QueryEngine/tools/*` (Tavily).

- **FR-20/21/22/23 – InsightEngine DB Search, Keyword Optimization, Sentiment**  
  - `InsightEngine/agent.py`, `InsightEngine/tools/*`, `InsightEngine/utils/db.py`.

- **FR-30/31 – MediaEngine Multimodal Analysis & Reflection**  
  - `MediaEngine/agent.py`, `MediaEngine/tools/*`.

- **FR-40/41/42 – ReportEngine**  
  - `ReportEngine/agent.py`, `ReportEngine/flask_interface.py`, `ReportEngine/nodes/*`.

- **FR-50/51/52 – ForumEngine**  
  - `ForumEngine/monitor.py` (LogMonitor), `ForumEngine/llm_host.py`.

- **FR-60/61 – Web UI & Streamlit Apps**  
  - `app.py`, `templates/index.html`, `SingleEngineApp/*`.

- **FR-70/71/72 – MindSpider Crawling**  
  - `MindSpider/main.py`, `MindSpider/BroadTopicExtraction/*`.

---

## 2. Modernization Requirement Traceability (MR-xx) - Planned

This section maps the new Modernization Requirements (MRs) to the target architecture (Stack A: LangGraph + Hatchet).

| Requirement ID | Requirement Name | Target Components | Implementation Status |
| :--- | :--- | :--- | :--- |
| **MR-01** | **International Data Integration** | `QueryEngine/tools/google_search.py`, `MediaEngine/tools/twitter_scraper.py`, `MediaEngine/tools/youtube_transcript.py` | **Pending** |
| **MR-02** | **Agent Collaboration (The Graph)** | `ForumEngine/graph/state.py` (State), `ForumEngine/graph/nodes/supervisor.py` (Router), `ForumEngine/graph/graph.py` (Compilation) | **In Design / Progress** |
| **MR-03** | **Real-time & Active Monitoring** | `hatchet.workflow` (Cron), `Watchlist` (Postgres Table), `SupervisorNode` (Diff Logic) | **Pending** |
| **MR-NFR-01** | **Observability & Traceability** | `Hatchet Dashboard` (Native), `LangSmith` (Optional integration) | **Implicit in Stack** |
| **MR-NFR-02** | **Reliability & Durability** | `Hatchet SDK` (Worker, Retries), `Postgres` (State Persistence) | **Implicit in Stack** |
| **MR-NFR-03** | **Scalability** | `bettafish-worker` (Distributed Service), Async Python | **Implicit in Stack** |

---

## 3. Known Gaps & Inconsistencies

### 3.1 Legacy System Gaps
*   **Authentication**: No auth on HTTP endpoints (FR-80 Gap).
*   **MindSpider UI**: No UI for crawling jobs (FR-81 Gap).
*   **Type Safety**: Loose typing in `Settings` and config handling.

### 3.2 Modernization Gaps (To Be Addressed)
*   **Missing Tools**: The `QueryEngine` and `MediaEngine` currently lack the actual implementation for Google Search, Twitter, and YouTube tools (MR-01).
*   **Legacy Wrappers**: The `AgentNode` wrappers need to carefully adapt the synchronous/subprocess nature of the old engines (or refactor them to be pure python classes) to work efficiently within the async Graph.
*   **Data Migration**: Plan needed for migrating any existing `MindSpider` data to the new schema if changes are required for international sources.

---

## 4. Recommended Next Steps

1.  **Implement the Core Graph**: Build `ForumState`, `SupervisorNode`, and the Agent Wrappers (MR-02).
2.  **Integrate Hatchet**: Set up the `hatchet.workflow` to trigger the graph (MR-NFR-02).
3.  **Develop New Tools**: Implement the Google/Twitter adapters to satisfy MR-01.
4.  **Build Watchlist**: Create the DB schema and Cron workflow for MR-03.