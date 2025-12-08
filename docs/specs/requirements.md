# Project Requirements: BettaFish Modernization

## 1. Overview
The goal is to modernize the existing BettaFish multi-agent system, transforming it from a fragile, file-based collaboration tool into a robust, scalable, and observable platform capable of real-time monitoring and international data gathering.

## 2. Modernization Functional Requirements (MR-xx)

### MR-01: International Data Integration
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

### MR-02: Agent Collaboration (The Graph)
*   **Orchestration**: Agents must collaborate via a structured **LangGraph StateGraph**, replacing the legacy file-based forum.
*   **Roles (Nodes)**:
    *   **QueryAgentNode**: Performs deep research (Web/News).
    *   **MediaAgentNode**: Gathers social sentiment/data (Legacy + New Sources).
    *   **InsightAgentNode**: Provides historical context from internal DBs.
    *   **SupervisorNode**: A routing node that moderates the discussion, identifies conflicts, and guides the research direction.
*   **Shared State**: All agents must read/write to a strictly typed `ForumState` (messages, findings, artifacts).
*   **Output**: A consolidated research report synthesizing findings from all agents.

### MR-03: Real-time & Active Monitoring
The system must actively monitor user-defined interests, not just respond to ad-hoc queries.

*   **Watchlist Management**:
    *   **Topics**: Users can subscribe to broad topics (e.g., "AI Agents", "Crypto Regulation").
    *   **Research Queries**: Users can monitor specific questions (e.g., "What is the latest version of LangGraph?").
*   **Active Polling**:
    *   The system must schedule background jobs (via Hatchet Cron) to check these sources at user-defined intervals.
*   **Smart Diffing & Alerting**:
    *   **Noise Reduction**: The system must compare new results against previous runs (stored in Postgres).
    *   **Significance Check**: Only trigger a full report or alert if *new* and *significant* information is found (LLM-based evaluation).
    *   **Notification**: Push alerts via WebSocket/Email when a significant update occurs.

## 3. Non-Functional Requirements (Modernization)

### MR-NFR-01: Observability & Traceability
*   **Visual Workflows**: Operators must be able to visualize the agent execution flow (DAG) in real-time via Hatchet UI.
*   **Traceability**: Every step (search query, crawl action, LLM call) must be logged and traceable to a Workflow Run ID.

### MR-NFR-02: Reliability & Durability
*   **Fault Tolerance**: Workflows must resume from the last successful step in case of system crash or restart (Durable Execution).
*   **State Persistence**: Agent state (conversation history, gathered data) must be persisted in a database (PostgreSQL).

### MR-NFR-03: Scalability
*   **Async Execution**: The system must handle multiple concurrent queries without blocking the main web server.
*   **Distributed Workers**: Background tasks (crawling, research) should be distributable across multiple worker nodes.

## 4. Technical Constraints & Stack Choices

### 4.1. Core Frameworks
*   **Workflow Engine**: **Hatchet** (Required).
    *   *Rationale*: Native Python async support, built-in observability UI, durable execution via Postgres.
*   **Agent Framework**: **LangGraph** (Selected).
    *   *Rationale*: Provides explicit control over state transitions, model agnosticism, and structured collaboration (See `stack_comparison.md`).
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

This section captures a concise FR/NFR snapshot for the **legacy/current BettaFish system**, ensuring traceability during migration.

### 6.1 Legend

- **FR‑xx** – Functional Requirements for the existing system.
- **NFR‑xx** – Non‑Functional Requirements for the existing system.
- **MR-xx** – Modernization Requirements (New).

### 6.2 Legacy Functional Requirements (FR‑xx)

**FR‑01 – End‑to‑End Analysis Workflow (implemented)**  
The system shall allow a user to trigger a full multi‑agent analysis and produce a consolidated report via the web UI.

**FR‑02 – Configurable Environment & Credentials (implemented)**  
The system shall load configuration from environment variables.

**FR‑03 – Docker & Source Deployments (implemented)**  
The system shall support both Docker‑based deployment and source‑based execution.

**FR‑10/11 – QueryEngine Search & Reflection (implemented)**  
The system shall provide a QueryEngine that performs multi‑step web/news search.

**FR‑20/21/22/23 – InsightEngine DB Search & Sentiment (implemented)**  
The system shall provide an InsightEngine that queries internal/private DBs.

**FR‑30/31 – MediaEngine Multimodal Analysis (implemented)**  
The system shall provide a MediaEngine that performs multimodal/web search.

**FR‑40/41/42 – ReportEngine (implemented)**  
The system shall select templates, build a Document IR, and render HTML/PDF.

**FR‑50/51/52 – ForumEngine (implemented)**  
The system shall monitor engine logs and host an LLM moderator.

**FR‑60/61 – Web UI & Streamlit Apps (implemented)**  
The system shall provide a unified Flask dashboard.

**FR‑70/71/72 – MindSpider Crawling (implemented)**  
The system shall initialize MindSpider’s DB and provide CLIs for topic extraction.

### 6.3 Legacy Non‑Functional Requirements (NFR‑xx)

**NFR‑01 – Resilient External API Calls (implemented)**  
**NFR‑02 – Robust Log Parsing & Tolerance (implemented)**  
**NFR‑10 – Async I/O & Streaming Responsiveness (partial)**  
**NFR‑20 – Secret & PII Handling (implemented)**  
**NFR‑30 – Logging, Tests & Config Governance (partial)**