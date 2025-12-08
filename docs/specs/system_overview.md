# System Overview – BettaFish (微舆)

This document summarizes the overall purpose, architecture, and runtime model of the BettaFish ("微舆") system, based on the current repository state.

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

## 2. High-Level Architecture

### 2.1 Major Engines (Agents)

The system centers on four primary analysis agents and a coordination forum:

- **InsightEngine** – Private Database Mining Agent
  - Analyzes internal/private opinion databases and structured/unstructured data.
  - Uses specialized tools for keyword optimization, DB querying, and sentiment analysis.
- **MediaEngine** – Multimodal Content Analysis Agent
  - Processes rich media content (e.g., short videos, images, text) from social platforms.
  - Extracts and interprets multi-modal signals as part of the overall analysis.
- **QueryEngine** – Broad Web & News Search Agent
  - Performs wide-ranging web and news search (domestic + international).
  - Collects contextual information, current events, and background knowledge.
- **ReportEngine** – Report Synthesis Agent
  - Aggregates outputs from other agents and the forum discussion.
  - Selects appropriate report templates and generates multi-round, structured reports.
- **ForumEngine** – Agent Collaboration Orchestrator
  - Monitors agent "forum" logs and coordinates debate/collaboration rounds.
  - Hosts a moderator LLM that summarizes and steers agent discussions.

### 2.2 Supporting Subsystems

- **MindSpider** – Crawling & Topic Extraction
  - Crawls Weibo and other sources for topics and sentiment signals.
  - Manages news/topic extraction and stores data in a relational database.
- **SentimentAnalysisModel** – Model Zoo
  - Provides multiple sentiment analysis approaches:
    - Fine-tuned BERT / GPT-2 models for Chinese opinion data.
    - Multilingual sentiment models for cross-language analysis.
    - Traditional ML models (SVM, XGBoost, etc.) for baseline/low-resource setups.
- **SingleEngineApp** – Streamlit-based Agent UIs
  - Exposes each primary engine (Insight/Media/Query) as an independent Streamlit app.
  - Useful for testing, demos, and single-agent use cases.
- **Flask Main App (`app.py`)**
  - Central web entrypoint that:
    - Manages configuration (via `.env` and `config.py` / Pydantic settings).
    - Starts/stops the three Streamlit apps.
    - Manages ForumEngine monitoring.
    - Exposes a unified search API that fans out user queries to running agents.
    - Registers ReportEngine’s Flask blueprint under `/api/report`.

---

## 3. Runtime & Deployment Model

### 3.1 Local / Source Execution

- **Process Model**:
  - `python app.py` runs the Flask + Socket.IO main server.
  - The main app can start three Streamlit processes (Insight, Media, Query) via `subprocess.Popen`, each listening on its own port (default 8501/8502/8503).
  - ForumEngine runs monitoring logic in-process (via imported `ForumEngine.monitor`) and writes to a `logs/forum.log` file.
  - ReportEngine is initialized (if available) through `ReportEngine.flask_interface` and exposed as a Flask blueprint.
- **Configuration**:
  - Centralized in `.env` and `config.py` (Pydantic settings), including:
    - DB connection parameters (dialect, host, port, user, password, database name, charset).
    - LLM API keys, base URLs, and model names per agent.
    - Search API keys (e.g., Tavily, Bocha web search).
  - `app.py` provides REST endpoints to read and update selected config settings at runtime.
- **User Access**:
  - Full system UI and controls via Flask front-end at `http://HOST:PORT` (default: `http://localhost:5000`).
  - Direct access to Streamlit apps for single-agent experiments using `streamlit run SingleEngineApp/...`.

### 3.2 Docker / Compose Deployment

- **`docker-compose.yml`** defines two core services:
  - `bettafish` service:
    - Runs the main application container (`ghcr.io/666ghj/bettafish:latest`).
    - Publishes ports:
      - `5000` for the Flask web app.
      - `8501/8502/8503` for the three Streamlit apps.
    - Mounts host directories:
      - `./logs` → `/app/logs` for runtime logs.
      - `./final_reports` → `/app/final_reports` for generated reports.
      - `./insight_engine_streamlit_reports`, `./media_engine_streamlit_reports`, `./query_engine_streamlit_reports` for agent-specific report outputs.
      - `./.env` → `/app/.env` for configuration.
  - `db` service:
    - PostgreSQL 15 database with default credentials (`bettafish` user/password/db).
    - Exposes `${POSTGRES_PORT:-5444}` on the host mapped to container port `5432`.
    - Persists data under `./db_data`.
- **Environment Requirements**:
  - Python 3.9+ (README examples use 3.11).
  - Postgres (preferred) or MySQL.
  - Playwright Chromium driver for crawling operations.

---

## 4. End-to-End Analysis Flow (Conceptual)

The README describes a typical complete analysis cycle as a multi-step, multi-agent workflow:

1. **User Question**
   - User submits a natural language query via the Flask web interface.
2. **Parallel Agent Startup**
   - QueryEngine, MediaEngine, and InsightEngine are started (or assumed running) and begin processing in parallel.
3. **Initial Broad Analysis**
   - Each agent performs a first-pass investigation using its specialized tools (web search, media analysis, DB queries, sentiment analysis, etc.).
4. **Strategy Planning**
   - Agents formulate a research strategy based on initial findings (what to explore further, what angles to cover).
5. **Forum-Based Deep Dive (Loop)**
   - In a loop of N rounds:
     - Agents perform deeper, targeted research.
     - ForumEngine monitors logs, aggregates agent outputs, and an LLM moderator produces summaries and guidance.
     - Agents adjust their direction based on the forum discussion and moderator feedback.
6. **Result Aggregation**
   - ReportEngine collects the final insights and key forum content.
7. **Report Generation**
   - ReportEngine selects an appropriate template from `ReportEngine/report_template/`.
   - Generates a structured, multi-section HTML report under `final_reports/`.

This flow is the basis for later functional requirements (e.g., FRs about starting agents, coordinating rounds, and generating reports).

---

## 5. Data & Persistence Overview

- **Databases**:
  - Primary relational database (PostgreSQL by default, MySQL supported via configuration):
    - Used by MindSpider for crawled topic/sentiment data.
    - Potentially used by InsightEngine for private datasets and aggregated opinion records.
  - Configuration relies on `DB_DIALECT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_CHARSET`.
- **File-Based Artifacts**:
  - `logs/` – Runtime logs for Streamlit apps and ForumEngine (`forum.log`).
  - `final_reports/` – Generated HTML reports (e.g., `final_report__YYYYMMDD_HHMMSS.html`).
  - Engine-specific `*_streamlit_reports/` directories for interactive report outputs.
- **External Services**:
  - OpenAI-compatible LLM providers for each engine (pluggable via `BASE_URL` + `MODEL_NAME`).
  - Search APIs (Tavily / Bocha) used by QueryEngine and potentially others.
  - Social media/web sites accessed via Playwright-based crawlers (MindSpider).

---

## 6. User-Facing Capabilities (High-Level)

From the current docs and app wiring, the system exposes the following high-level capabilities:

- **Interactive Web UI**
  - Launch and monitor the full multi-agent system from a single Flask interface.
  - View logs and live console outputs for each component.
  - Trigger searches and observe collaborative reasoning in near real time.
- **Agent-Specific UIs (Streamlit)**
  - Run each major engine independently with its own specialized UI.
- **Automated Crawling & Topic Discovery**
  - Use MindSpider to crawl social platforms, extract trending topics, and store data for analysis.
- **Sentiment Analysis Toolkit**
  - Evaluate sentiment using different model families depending on resource constraints and language needs.
- **Report Generation**
  - Produce structured, human-readable reports tailored to use-cases (brand reputation, competitive landscape, policy events, etc.) using customizable templates.

These points will be refined into explicit functional requirements in `requirements.md` (e.g., FR-01: "The system shall allow users to submit natural-language queries via the web UI and trigger an end-to-end analysis workflow").

---

## 7. Non-Functional Considerations (Snapshot)

The current implementation and docs imply several non-functional aspects:

- **Modularity & Extensibility**
  - Engines follow a similar structure (agents, nodes, tools, utils), enabling new tools/models to be plugged in with minimal changes.
- **Deployment Flexibility**
  - Supports both local source execution and Docker-based deployment.
- **Observability**
  - Logs for each process and a dedicated forum log make it possible to trace multi-agent interactions.
- **Internationalization**
  - Multi-language sentiment models and web search across domestic/international sources.
- **Resource Awareness**
  - Separation of crawling, analysis, and reporting allows scaling components independently (especially in Docker setups).

These will be turned into formal NFRs (e.g., NFR-01..NFR-xx) in the dedicated requirements spec.

---

## 8. Links to Detailed Specs

This overview connects to the rest of the spec-driven documentation under `docs/specs/`:

- `spec_discovery_and_requirements_flow.md` – Process and methodology for extracting specs and requirements.
- `component_map.md` – Detailed breakdown of modules, classes, and responsibilities.
- `interfaces_and_integrations.md` – HTTP APIs, CLIs, data stores, and external services.
- `behavioral_expectations.md` – Expected behaviours, edge cases, and invariants derived from tests and real logs.
- `requirements.md` – Formal functional and non-functional requirements (planned; to be added).
- `traceability_and_gaps.md` – Mapping between requirements and implementation, plus known gaps and open questions.
