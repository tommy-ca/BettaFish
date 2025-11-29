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
