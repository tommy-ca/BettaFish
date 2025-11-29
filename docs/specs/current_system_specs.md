# Current System Specifications

## 1. System Architecture & Data Flow

### High-Level Architecture
The system operates as a loosely coupled multi-agent system where agents run independently and "collaborate" via a shared log-based forum.

*   **Frontend**: Flask + Streamlit (for individual engine debugging).
*   **Backend**: Python-based independent agent processes.
*   **Communication**: File-based log monitoring (`ForumEngine`).
*   **Database**: MySQL/PostgreSQL (structured data) + Redis (implied for caching).

### Data Flow
1.  **Input**: User query triggers the system.
2.  **Parallel Execution**: `QueryEngine`, `MediaEngine`, and `InsightEngine` start their tasks.
3.  **Agent Output**: Each agent writes its progress and findings to its own log file (`query.log`, `media.log`, `insight.log`).
4.  **Forum Aggregation**:
    *   `ForumEngine` (specifically `LogMonitor`) watches these log files.
    *   It extracts structured content (JSON) or summaries using regex patterns (e.g., detecting `FirstSummaryNode`).
    *   Extracted content is written to a central `forum.log`.
5.  **Moderation (The "Host")**:
    *   `ForumHost` (LLM-based) monitors `forum.log`.
    *   After a threshold of agent messages (default: 5), it generates a synthesis/guidance speech.
    *   This speech is written back to `forum.log` for agents to potentially read (though agent consumption of host feedback seems implicit or manual in current code).
6.  **Reporting**: `ReportEngine` aggregates the final state from the forum or agents to generate the report.

## 2. Component Specifications

### A. Search (QueryEngine)
*   **Core Logic**: `QueryEngine/agent.py` implements a "Planner + Execution" pattern.
*   **Workflow**:
    1.  **Structure Generation**: LLM generates a report outline (paragraphs).
    2.  **Paragraph Processing**: For each paragraph:
        *   **Search**: Generates queries, selects tools.
        *   **Summary**: Summarizes search results.
        *   **Reflection Loop**: Critiques the summary, generates new queries, searches again, and updates.
    3.  **Final Report**: Aggregates paragraph summaries.
*   **Tools**: `TavilyNewsAgency` (Wrapper for Tavily API).
    *   `basic_search_news`: General news search.
    *   `deep_search_news`: AI-optimized deep search.
    *   `search_news_by_date`: Time-bounded search.
*   **State Management**: In-memory `State` object, optionally saved to JSON.

### B. Media Channels (MindSpider)
*   **Core Logic**: `MindSpider/main.py` orchestrates crawling.
*   **Architecture**:
    *   **BroadTopicExtraction**: Scrapes news sites for trending topics.
    *   **DeepSentimentCrawling**: Targeted crawling based on topics/keywords.
*   **Crawler Implementation**:
    *   **Base**: `AbstractCrawler` pattern.
    *   **Engine**: `Playwright` (browser automation) + `httpx` (API).
    *   **Anti-Scraping**: `stealth.min.js`, random delays, CDP (Chrome DevTools Protocol) mode.
    *   **Concurrency**: `asyncio.Semaphore` limits concurrent tabs/requests.
*   **Supported Platforms & Specs**:
    *   **Weibo**: Notes, Comments, Creator Info.
    *   **Xiaohongshu (XHS)**: Notes (with `xsec_token`), Comments, Creator Info.
    *   **Bilibili**: Video info, Comments, Up (Creator) Info.
    *   **Douyin/Kuaishou**: Short video metadata, comments.
    *   **Tieba/Zhihu**: Forum posts, Q&A, comments.
*   **Data Schema**:
    *   Platform-specific tables (e.g., `xhs_note`, `weibo_comment`) linked to `daily_topics`.

### C. Forum Collaboration (ForumEngine)
*   **Mechanism**: Log-based "Blackboard" pattern.
*   **LogMonitor**:
    *   Watches `insight.log`, `media.log`, `query.log`.
    *   Regex-based extraction of JSON outputs from `SummaryNode`s.
    *   Handles log rotation/truncation.
*   **ForumHost**:
    *   **Model**: Qwen3-235B (via SiliconFlow).
    *   **Role**: Summarizes events, identifies conflicts, guides discussion.
    *   **Trigger**: Every 5 agent messages.

## 3. Key Observations for Modernization
*   **Fragility**: The regex-based log parsing in `ForumEngine` is brittle. A change in log format breaks the collaboration.
*   **State**: State is fragmented across log files and individual agent memory.
*   **Opportunity**: **LangGraph** is a perfect fit to replace `ForumEngine`.
    *   The "Forum" becomes a shared `StateGraph`.
    *   Agents become nodes.
    *   The "Host" becomes a conditional edge or a supervisor node.
    *   Log parsing is replaced by structured state passing.
