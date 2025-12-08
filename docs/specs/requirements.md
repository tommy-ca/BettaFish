# Project Requirements: BettaFish Modernization

## 1. Overview
The goal is to modernize the existing BettaFish multi-agent system, transforming it from a fragile, file-based collaboration tool into a robust, scalable, and observable platform capable of real-time monitoring and international data gathering.

## 2. Functional Requirements

### 2.1. International Data Integration
The system must support data collection from the following international sources:
*   **Search Engines**:
    *   **Google Search**: For broad, real-time news and information.
    *   **Exa (Metaphor)**: For neural/semantic search to find thematically related content.
    *   **Firecrawl**: For deep scraping of specific URLs into clean markdown.
*   **Social Media**:
    *   **Twitter/X**: "Advanced Search" scraping for specific topics/hashtags.
    *   **YouTube**: Video transcripts (`youtube-transcript-api`) and metadata (`yt-dlp`).
    *   **Reddit**: Subreddit and keyword monitoring via PRAW.
    *   **Podcasts**: Audio transcription via OpenAI Whisper from RSS feeds.
*   **Legacy Sources (Must Maintain)**:
    *   Weibo, Xiaohongshu (XHS), Bilibili, Douyin, Kuaishou, Tieba, Zhihu.

### 2.2. Agent Collaboration ("The Forum")
*   **Orchestration**: Agents must collaborate in a structured debate format.
*   **Roles**:
    *   **QueryAgent**: Performs deep research.
    *   **MediaAgent**: Gathers social sentiment/data.
    *   **InsightAgent**: Provides historical context.
    *   **Supervisor (Host)**: Moderates the discussion, identifies conflicts, and guides the research direction.
*   **Output**: A consolidated research report synthesizing findings from all agents.

### 2.3. Real-time & Active Monitoring
The system must actively monitor user-defined interests, not just respond to ad-hoc queries.

*   **Watchlist Management**:
    *   **Topics**: Users can subscribe to broad topics (e.g., "AI Agents", "Crypto Regulation").
    *   **Research Queries**: Users can monitor specific questions (e.g., "What is the latest version of LangGraph?").
*   **Active Polling**:
    *   The system must schedule background jobs to check these sources at user-defined intervals (e.g., "Every 15 minutes", "Daily").
*   **Smart Diffing & Alerting**:
    *   **Noise Reduction**: The system must compare new results against previous runs.
    *   **Significance Check**: Only trigger a full report or alert if *new* and *significant* information is found (LLM-based evaluation).
    *   **Notification**: Push alerts via WebSocket/Email when a significant update occurs.

## 3. Non-Functional Requirements

### 3.1. Observability
*   **Visual Workflows**: Operators must be able to visualize the agent execution flow (DAG) in real-time.
*   **Traceability**: Every step (search query, crawl action, LLM call) must be logged and traceable.
*   **Debugging**: Support for "time travel" or replaying workflow steps from a specific state.

### 3.2. Reliability & Durability
*   **Fault Tolerance**: Workflows must resume from the last successful step in case of system crash or restart.
*   **State Persistence**: Agent state (conversation history, gathered data) must be persisted in a database (PostgreSQL), not just in-memory or log files.

### 3.3. Scalability
*   **Async Execution**: The system must handle multiple concurrent queries without blocking.
*   **Distributed Workers**: Background tasks (crawling, research) should be distributable across multiple worker nodes.

## 4. Technical Constraints & Stack Choices

### 4.1. Core Frameworks
*   **Workflow Engine**: **Hatchet** (Required).
    *   *Rationale*: Native Python async support, built-in observability UI, durable execution via Postgres.
*   **Agent Framework**: Two supported options (See `stack_comparison.md`):
    1.  **Claude Agent SDK**: Best for open-ended research with Claude 3.5.
    2.  **LangGraph**: Best for rigid control flow and model agnosticism.
*   **Language**: Python 3.9+.

### 4.2. Infrastructure
*   **Database**: PostgreSQL (Primary State Store), Redis (Caching/Broker if needed).
*   **Browser Automation**: Playwright (for scraping).

## 5. Migration Requirements
*   **Phased Approach**:
    1.  **Wrap**: Port existing logic to LangGraph nodes without full rewrite.
    2.  **Expand**: Add international sources.
    3.  **Scale**: Integrate Hatchet for background execution.
*   **Backward Compatibility**: The existing Flask API structure should be maintained where possible, but updated to support async task submission.

---

## 6. Current System FR/NFR Reference

The sections above describe **modernization requirements** for the future architecture (Hatchet + Agent SDK stack). This section captures a concise FR/NFR snapshot for the **current BettaFish system as implemented in this repo**, so that specs, traceability, and modernization work share a common vocabulary.

### 6.1 Legend

- **FR‑xx** – Functional Requirements for the existing system.
- **NFR‑xx** – Non‑Functional Requirements for the existing system.
- **Status**: implemented / partial / gap (planned).

See `traceability_and_gaps.md` for detailed mappings from these IDs to concrete modules.

### 6.2 Functional Requirements (FR‑xx)

**FR‑01 – End‑to‑End Analysis Workflow (implemented)**  
The system shall allow a user to trigger a full multi‑agent analysis and produce a consolidated report via the web UI.

**FR‑02 – Configurable Environment & Credentials (implemented)**  
The system shall load configuration (DB, LLM, search API keys, base URLs, model names, etc.) from environment variables and expose a limited set for runtime inspection/update.

**FR‑03 – Docker & Source Deployments (implemented)**  
The system shall support both Docker‑based deployment (via `docker-compose.yml`) and source‑based execution (via `python app.py` + Streamlit CLIs).

**FR‑10/11 – QueryEngine Search & Reflection (implemented)**  
The system shall provide a QueryEngine that performs multi‑step web/news search and reflection‑based summarization using Tavily‑like tools.

**FR‑20/21/22/23 – InsightEngine DB Search, Keyword Optimization, Sentiment (implemented / partial)**  
The system shall provide an InsightEngine that queries internal/private DBs, supports keyword optimization, performs optional sentiment analysis via `SentimentAnalysisModel`, and maintains per‑paragraph research state.

**FR‑30/31 – MediaEngine Multimodal Analysis & Reflection (implemented)**  
The system shall provide a MediaEngine that performs multimodal/web search (via Bocha tools) and reflection‑based summarization.

**FR‑40/41/42 – ReportEngine (implemented, with noted task‑semantics gaps)**  
The system shall select templates, build a Document IR from engine reports + `forum.log`, render HTML (and optionally PDF), persist artifacts, and expose HTTP/SSE APIs for report tasks.

**FR‑50/51/52 – ForumEngine (implemented)**  
The system shall monitor engine logs, extract SummaryNode outputs, build a normalized forum log, and host an LLM moderator whose guidance is also logged and surfaced to the UI.

**FR‑60/61 – Web UI & Streamlit Apps (implemented)**  
The system shall provide a unified Flask dashboard with Socket.IO streaming plus per‑engine Streamlit apps and `/api/search` endpoints.

**FR‑70/71/72 – MindSpider Crawling (implemented)**  
The system shall initialize MindSpider’s DB on system start and provide CLIs for topic extraction and deep sentiment crawling across platforms.

**FR‑80 – HTTP Auth & Access Control (gap)**  
The system should provide authentication and/or access control for HTTP and SSE/WebSocket endpoints when deployed beyond localhost.

**FR‑81 – MindSpider Operations from Web UI (gap)**  
The system should expose basic MindSpider operations (e.g., `--broad-topic`, `--deep-sentiment`) via the main dashboard or REST.

### 6.3 Non‑Functional Requirements (NFR‑xx)

**NFR‑01 – Resilient External API Calls (implemented/ongoing)**  
External LLM/search API calls shall use standardized retry and backoff policies (e.g., `with_graceful_retry`).

**NFR‑02 – Robust Log Parsing & Tolerance (implemented)**  
ForumEngine log parsing shall tolerate legacy and loguru formats, handle malformed JSON gracefully, and avoid polluting forum content with error logs.

**NFR‑10 – Async I/O & Streaming Responsiveness (partial)**  
The system should keep log and forum streaming responsive under normal workloads (child process streaming + Socket.IO + SSE), though no explicit throughput/latency SLAs are defined.

**NFR‑20 – Secret & PII Handling (implemented, requires discipline)**  
Secrets (API keys, DB passwords) shall be sourced from environment/`.env` and not hardcoded; logs should avoid including secrets or unnecessary PII.

**NFR‑30 – Logging, Tests & Config Governance (partial)**  
The system should maintain consistent logging, central configuration via `Settings`, and focused automated tests for critical paths (currently strongest for ForumEngine; some for ReportEngine sanitization).

**NFR‑40 – Config Validation & Fail‑Fast Behavior (gap/partial)**  
The system should validate required configuration at startup and fail fast with clear messages when misconfigured, instead of surfacing lower‑level runtime errors.

**NFR‑41 – User‑Visible Error Messages & Status Indicators (gap/partial)**  
The UI and APIs should clearly surface which subsystems (ReportEngine, MindSpider, etc.) are unavailable and why.

**NFR‑42 – Task Lifecycle Transparency (partial)**  
Long‑running tasks (especially reports) should expose clear lifecycle states (`running`, `completed`, `error`, `cancelled`, `not‑found`) to clients.

**NFR‑50 – Automated Test Coverage for Core Flows (gap/partial)**  
Core workflows (ReportEngine, agent pipelines, sentiment integration) should be covered by automated tests beyond the existing ForumEngine suite.

**NFR‑60 – Performance & Resource Constraints Specification (gap)**  
The system should document and, where possible, enforce reasonable performance and resource usage expectations (e.g., end‑to‑end latency targets, token budgets, concurrency limits).

