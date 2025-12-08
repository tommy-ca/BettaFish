# System Overview – BettaFish (微舆)

This document summarizes the overall purpose, architecture, and runtime model of the BettaFish ("微舆") system. It describes both the **Legacy (Current)** architecture and the **Modernization (In Progress)** architecture.

---

## 1. Purpose & Core Value

- **Problem Space**: Public-opinion (舆情) analysis across domestic and international social media and web sources. Users can ask natural-language questions and obtain in-depth analytical reports.
- **Goal**: Provide an AI-driven, multi-agent analysis platform that:
  - Breaks information silos and presents a holistic view of topics/brands/events.
  - Combines broad web/media search, private data mining, sentiment analysis, and report generation.
  - Supports extension to other domains (e.g., finance) by adjusting tools and prompts.
- **Target Users**:
  - Analysts and organizations monitoring brand reputation, public events, policy feedback.
  - Developers who want a reference implementation of a multi-agent, LLM-based analysis system.

---

## 2. High-Level Architecture (Modernization)

We are actively migrating to a robust, scalable stack ("Stack A"):

- **Orchestration**: **LangGraph**.
  - Replaces the fragile file-based forum with a structured `StateGraph`.
  - Defines explicit nodes (`SupervisorNode`, `QueryAgentNode`) and a strictly typed `ForumState`.
- **Execution**: **Hatchet**.
  - Provides durable execution, retries, and distributed background workers.
  - Manages cron schedules for active monitoring.
- **Data Sources**:
  - Adding International sources: Google Search, Twitter/X, YouTube.
  - Maintaining Legacy sources: Weibo, XHS, etc. via `MindSpider`.

*See `docs/specs/architecture_design_langgraph.md` for the detailed design.*

---

## 3. Legacy Architecture (Current Runtime)

### 3.1 Major Engines (Agents)

The system centers on four primary analysis agents and a coordination forum:

- **InsightEngine** – Private Database Mining Agent
- **MediaEngine** – Multimodal Content Analysis Agent
- **QueryEngine** – Broad Web & News Search Agent
- **ReportEngine** – Report Synthesis Agent
- **ForumEngine** – Agent Collaboration Orchestrator (Legacy file-based monitor)

### 3.2 Runtime Model

- **Process Model**:
  - `python app.py` runs the Flask + Socket.IO main server.
  - Streamlit apps run as subprocesses.
  - ForumEngine monitors `logs/*.log` via regex.
- **Deployment**:
  - Supports both local source execution and Docker-based deployment (`docker-compose.yml`).

---

## 4. End-to-End Analysis Flow (Conceptual)

1. **User Question**: Submitted via Web UI.
2. **Parallel Agent Startup**: Agents begin processing in parallel.
3. **Initial Broad Analysis**: First-pass investigation using specialized tools.
4. **Strategy Planning**: Agents formulate a research strategy.
5. **Forum-Based Deep Dive (Loop)**:
   - **Legacy**: Log-based forum monitoring and LLM host guidance.
   - **Modern**: `SupervisorNode` analyzes state and routes execution to specific agents.
6. **Result Aggregation**: ReportEngine collects final insights.
7. **Report Generation**: Structured HTML report generation.

---

## 5. Documentation Map

*   **Requirements**: `docs/specs/requirements.md` (See `MR-xx` for new reqs).
*   **Architecture**: `docs/specs/architecture_design_langgraph.md` (New Design).
*   **Components**: `docs/specs/component_map.md`.
*   **Interfaces**: `docs/specs/interfaces_and_integrations.md`.
*   **Implementation Plan**: `docs/specs/implementation_plan_langgraph.md`.