# Implementation Plan: BettaFish Modernization (Claude SDK + Hatchet)

# Goal
Modernize BettaFish by replacing the legacy custom agent system with **Claude Agent SDK** for intelligence and **Hatchet** for orchestration, enabling international data support and real-time monitoring.

## User Review Required
> [!IMPORTANT]
> **API Keys Required**: Ensure you have keys for Anthropic (`ANTHROPIC_API_KEY`), Tavily, Exa, and Twitter/Google (if using official APIs).
> **PostgreSQL**: Hatchet requires a PostgreSQL database. Ensure connection details are available.

## Proposed Changes

### Phase 1: Foundation & Tools
Set up the environment and build the fundamental tools for the agents.

#### 1. Environment Setup
-   [ ] Install `claude-agent-sdk`, `hatchet-sdk`, `playwright`.
-   [ ] Configure `hatchet` server (local or cloud) and worker.

#### 2. Tool Implementation (Claude SDK)
Implement data sources as tools compatible with Claude SDK.
-   [ ] **Search Tools**: `GoogleSearchTool`, `ExaSearchTool`, `TavilyTool` (Legacy).
-   [ ] **Social Tools**: `TwitterScraperTool` (Playwright), `YoutubeTool`.
-   [ ] **Legacy Social Tools**: Wrap `MindSpider` crawlers (`WeiboTool`, `XHSTool`, `BilibiliTool`).
-   [ ] **Database Tools**: `InsightTool` (Read access to existing SQL DB).

### Phase 2: The Agents (Claude SDK)
Implement the intelligence layer using Claude Agent SDK.

#### 1. Subagents
-   [ ] **QueryAgent**: Specialized in using Search Tools to answer questions.
-   [ ] **MediaAgent**: Specialized in using Social Tools to gather sentiment.

#### 2. Supervisor Agent
-   [ ] **Supervisor**: The main entry point.
    -   System Prompt: "You are a research coordinator..."
    -   Tools: Can call `QueryAgent` and `MediaAgent`.
    -   Logic: Loop until comprehensive answer is found.

### Phase 3: Orchestration (Hatchet)
Wrap the agents in durable workflows.

#### 1. Workflows
-   [ ] **`ResearchWorkflow`**:
    -   Input: `query` (str).
    -   Step: Initialize `SupervisorAgent`.
    -   Step: Run Agent.
    -   Step: Run Agent.
    -   Step: Return/Save result.
    -   Step: Call `ReportEngine` to generate PDF/HTML.

#### 2. Monitoring (Active Watchlist)
-   [ ] **Database**: Create `watchlist` table (Postgres).
-   [ ] **`MonitorWorkflow`**:
    -   Cron: Every 15 mins.
    -   Step: Fetch active items.
    -   Step: Run Agent (Light mode) to get current status.
    -   Step: **Diff**: Compare with `last_snapshot`.
    -   Step: If significant, trigger `ResearchWorkflow`.

### Phase 4: API & Integration
Expose the new system to the frontend.

#### 1. Flask API
-   [ ] Update `/api/search` to trigger `hatchet.run_workflow`.
-   [ ] Add `/api/tasks/{id}` to poll Hatchet status.

## Verification Plan

### Automated Tests
-   **Unit Tests**: Test individual Tools (e.g., does `GoogleSearchTool` return results?).
-   **Integration Tests**: Run a full `ResearchWorkflow` with a mock query and verify it completes in Hatchet.

### Manual Verification
-   **Hatchet UI**: Visually inspect the workflow execution graph.
-   **Output Check**: Verify the final report contains data from the new international sources.
