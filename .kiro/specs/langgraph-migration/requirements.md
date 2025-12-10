# Requirements Document

## Introduction
The goal is to modernize the existing BettaFish multi-agent system, transforming it from a fragile, file-based collaboration tool into a robust, scalable, and observable platform capable of real-time monitoring and international data gathering. This specification covers the migration to a stack using LangGraph for agent orchestration and Hatchet for durable execution.

## Requirements

### Requirement 1: International Data Integration
**Objective:** As a Researcher, I want to collect data from international sources like Google, Twitter, and Reddit, so that I have a comprehensive view of the topic.

#### Acceptance Criteria
1. The BettaFish System shall support data collection from search engines including Google Search, Exa (Metaphor), and Firecrawl.
2. The BettaFish System shall support data collection from social media platforms including Twitter/X, YouTube (transcripts and metadata), and Reddit.
3. The BettaFish System shall support audio transcription from Podcasts via OpenAI Whisper.
4. The BettaFish System shall maintain support for legacy sources including Weibo, Xiaohongshu, Bilibili, Douyin, Kuaishou, Tieba, and Zhihu.

### Requirement 2: Agent Collaboration (LangGraph)
**Objective:** As a Developer, I want agents to collaborate via a structured state graph, so that the workflow is deterministic and observable.

#### Acceptance Criteria
1. The Agent Orchestrator shall use LangGraph StateGraph for agent coordination, replacing the legacy file-based forum.
2. The System shall implement a QueryAgentNode for deep web and news research.
3. The System shall implement a MediaAgentNode for social sentiment and data gathering from both legacy and new sources.
4. The System shall implement an InsightAgentNode for providing historical context from internal databases.
5. The System shall implement a SupervisorNode to route messages, identify conflicts, and guide the research direction.
6. All Agents shall read and write to a strictly typed `ForumState` containing messages, findings, and artifacts.
7. The System shall produce a consolidated research report synthesizing findings from all agents.

### Requirement 3: Real-time & Active Monitoring
**Objective:** As a User, I want to subscribe to topics and receive alerts, so that I stay updated without manual queries.

#### Acceptance Criteria
1. The System shall allow users to subscribe to broad topics and specific research queries.
2. The System shall schedule background jobs via Hatchet Cron to poll sources at user-defined intervals.
3. When new results are found, the System shall compare them against previous runs stored in Postgres.
4. If new and significant information is found, the System shall trigger a full report or alert.
5. The System shall send push alerts via WebSocket or Email when a significant update occurs.

### Requirement 4: Observability & Traceability
**Objective:** As an Operator, I want to visualize workflows and trace execution, so that I can debug and monitor performance.

#### Acceptance Criteria
1. The System shall provide real-time workflow visualization via Hatchet UI.
2. The System shall log every step (search query, crawl action, LLM call) with a unique Workflow Run ID.

### Requirement 5: Reliability & Durability
**Objective:** As an Operator, I want workflows to resume after failures, so that long-running tasks are not lost.

#### Acceptance Criteria
1. If the system crashes or restarts, the Workflow Engine shall resume execution from the last successful step (Durable Execution).
2. The System shall persist agent state (conversation history, gathered data) in PostgreSQL.

### Requirement 6: Scalability
**Objective:** As a System Architect, I want to handle concurrent queries and distribute work, so that the system scales with load.

#### Acceptance Criteria
1. The System shall handle multiple concurrent queries asynchronously without blocking the main web server.
2. The System shall support distributed workers for background tasks such as crawling and research.

### Requirement 7: Migration Strategy
**Objective:** As a Developer, I want a phased migration, so that existing functionality is preserved while new features are added.

#### Acceptance Criteria
1. The System shall wrap existing logic into LangGraph nodes where possible to avoid full rewrites in the first phase.
2. The System shall maintain the existing Flask API structure while updating it to support async task submission.