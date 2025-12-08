# Traceability & Gaps – BettaFish

This document maps high-level requirements to their implementing components and records known gaps or open questions. It is intentionally lightweight and will grow as more detailed specs and tests are added. See `requirements.md` §6 for concise definitions of FR‑xx/NFR‑xx used here.

---

## 1. Requirement → Component Traceability (Initial)

This table summarizes where key requirements are primarily implemented. Many requirements span multiple modules; listed modules are the main loci.

- **FR-01 – End-to-End Analysis Workflow**  
  - Main components:
    - `app.py` (system orchestration, HTTP endpoints).  
    - `QueryEngine/agent.py` (DeepSearchAgent).  
    - `MediaEngine/agent.py` (DeepSearchAgent).  
    - `InsightEngine/agent.py` (DeepSearchAgent).  
    - `ForumEngine/monitor.py`, `ForumEngine/llm_host.py` (forum aggregation & host).  
    - `ReportEngine/agent.py`, `ReportEngine/flask_interface.py` (report synthesis).  

- **FR-02 – Configurable Environment & Credentials**  
  - `config.py` (Pydantic Settings and `.env` reading).  
  - `app.py` (`read_config_values`, `write_config_values`, `/api/config`).

- **FR-03 – Docker & Source Deployments**  
  - `docker-compose.yml` (container wiring, volumes, DB).  
  - `Dockerfile` (image build).  
  - `README.md` / `README-EN.md` (source installation instructions).

- **FR-10/11 – QueryEngine Search & Reflection**  
  - `QueryEngine/agent.py` (search tool invocation, reflection loops).  
  - `QueryEngine/tools/*` (Tavily wrapper and types).  
  - `QueryEngine/nodes/*` (search, summary, structure, formatting nodes).  
  - `QueryEngine/state/*` (state model for paragraphs/reports).

- **FR-20/21/22/23 – InsightEngine DB Search, Keyword Optimization, Sentiment**  
  - `InsightEngine/agent.py` (DB tool invocation, reflection loops, integration of keyword optimizer and sentiment analyzer).  
  - `InsightEngine/tools/keyword_optimizer.py` (keyword optimization middleware).  
  - `InsightEngine/tools/search.py` and `InsightEngine/tools/*` (DB search tools).  
  - `InsightEngine/utils/db.py` (async DB access).  
  - `InsightEngine/tools/sentiment_analyzer.py` (integration with SentimentAnalysisModel).  
  - `SentimentAnalysisModel/*` (actual models and CLIs).

- **FR-30/31 – MediaEngine Multimodal Analysis & Reflection**  
  - `MediaEngine/agent.py` (DB-backed media search & reflection loops).  
  - `MediaEngine/tools/*` (media DB wrapper, keyword optimizer, possibly vision-related helpers).  
  - `MediaEngine/nodes/*` (media-specific summary and structure nodes).

- **FR-40/41/42 – ReportEngine**  
  - `ReportEngine/agent.py` (`ReportAgent`, `FileCountBaseline`, template selection, document layout/word budget planning, chapter generation, IR composition, HTML/PDF rendering, saving).  
  - `ReportEngine/flask_interface.py` (Blueprint, `ReportTask`, `/status`, `/generate`, `/progress`, `/result`, `/download`, `/cancel`, `/templates`, `/log*`, `/export/pdf/*` endpoints).  
  - `ReportEngine/nodes/*` (`TemplateSelectionNode`, `DocumentLayoutNode`, `WordBudgetNode`, `ChapterGenerationNode`).  
  - `ReportEngine/core/*`, `ReportEngine/ir/*`, `ReportEngine/renderers/*`, `ReportEngine/state/*` (template parsing, chapter storage, IR stitching, rendering, task/state models).  
  - `ReportEngine/report_template/*` (Markdown templates).

- **FR-50/51/52 – ForumEngine**  
  - `ForumEngine/monitor.py` (`LogMonitor`, log parsing, JSON extraction, forum session lifecycle, host triggering).  
  - `ForumEngine/llm_host.py` (`ForumHost`, Qwen API calls).  
  - `tests/test_monitor.py`, `tests/forum_log_test_data.py` (behavioral tests).  
  - `utils/forum_reader.py` (agents reading forum outputs).

- **FR-60/61 – Web UI & Streamlit Apps**  
  - `app.py` (Flask + Socket.IO entrypoint, controlling apps).  
  - `templates/index.html`, `static/*` (UI).  
  - `SingleEngineApp/*_streamlit_app.py` (per-engine Streamlit frontends and `/api/search` endpoints).  

- **FR-70/71/72 – MindSpider Crawling**  
  - `MindSpider/main.py`, `MindSpider/config.py.example` (CLI entrypoint and config).  
  - `MindSpider/BroadTopicExtraction/*` (topic extraction).  
  - `MindSpider/DeepSentimentCrawling/*` (deep crawling and platform-specific crawlers).  
  - `MindSpider/schema/*` (DB schema & initialization).  
  - `app.py` (calls `MindSpider.MindSpider.initialize_database()` in `initialize_system_components`).

- **NFRs (Selected Mappings)**  
  - **NFR-01 (retries)**: `utils/retry_helper.py`, `ForumEngine/llm_host.py` (`with_graceful_retry` on LLM calls), search tools.  
  - **NFR-02 (log parsing tolerance)**: `ForumEngine/monitor.py` (`extract_json_content`, `fix_json_string`, `is_target_log_line`).  
  - **NFR-10/11/12 (performance/async/streaming)**:  
    - Async DB: `InsightEngine/utils/db.py`.  
    - Search limits: `QueryEngine.utils.config.Settings`, `InsightEngine.utils.config.Settings`.  
    - Streaming logs: `app.py` + Socket.IO + `monitor_forum_log`.  
  - **NFR-20/21 (secrets & PII)**: `config.py`, `.env.example`, lack of hardcoded keys.  
  - **NFR-30/31/32 (logging, tests, config)**: widespread `loguru` usage; `tests/test_monitor.py`; `Settings` classes for each engine.

---

## 2. Known Gaps & Inconsistencies (Initial)

This section lists notable gaps between the requirements and the current implementation, or areas where behavior is unclear.

### 2.1 Authentication & Access Control

- Current state:
  - No authentication/authorization is enforced on HTTP endpoints (Flask main app or ReportEngine).  
  - Docker configuration exposes ports directly without reverse proxy or auth.
- Impact:
  - For production deployments, additional layers (reverse proxy, API gateway, auth middleware) are required to satisfy typical security requirements.
- Status:
  - Gap relative to future FRs/NFRs; acceptable for a research/demo system.

### 2.2 Error Handling & User Feedback

- Some endpoints only return generic error messages when underlying exceptions occur (e.g., LLM/API failures, DB connectivity issues).  
- The main app logs type-check issues (e.g., possibly-unbound `report_bp` when ReportEngine import fails) but the user-facing UI may not clearly indicate which sub-system is unavailable.
- Potential improvement:
  - Add explicit status indicators in `/api/status` and UI for ReportEngine and MindSpider readiness.

### 2.3 Type & Config Safety

- Static analysis diagnostics indicate potential type issues, such as:
  - `settings.*` values potentially `None` being passed into classes expecting `str` (e.g., LLM clients, DB URL builder).  
  - Some functions returning `Optional[str]` but annotated as `str` (`InsightEngine/utils/db.py._build_database_url`).
- Impact:
  - At runtime, missing config may cause errors that are not guarded by explicit checks.
- Potential improvement:
  - Strengthen validation in `Settings` classes and fail fast with clear messages when required config is missing.

### 2.4 ReportEngine Task Cleanup Semantics

- `ReportEngine/flask_interface.py` cleans up `current_task` on errors and when creating new tasks, but `/progress/<task_id>` fabricates a "completed" task when a task is not found.  
- This behavior is convenient for polling, but may hide underlying failures or cancellations.
- Potential improvement:
  - Distinguish between `not-found-because-cleaned-up` vs `never-existed` vs `cancelled`, or provide richer status history.

### 2.5 MindSpider Integration Depth

- While `app.py` initializes MindSpider’s DB, there is no direct UI or API integration for running crawling jobs from the main dashboard.
- MindSpider is currently operated via CLI; deeper integration might be desired for a fully unified UX.

### 2.6 Test Coverage Beyond ForumEngine

- Current explicit tests are strongest around `ForumEngine/monitor.py` log parsing; there is some coverage for ReportEngine sanitization (`tests/test_report_engine_sanitization.py`), but end-to-end report generation behavior remains largely untested.  
- There is still limited coverage for:
  - Report template selection, layout/word-budget planning, and chapter/IR generation contracts.  
  - QueryEngine/InsightEngine reflection loops and search tool selection.  
  - Sentiment analysis integration behavior and failure modes.
- Potential improvement:
  - Add targeted tests using small synthetic inputs to validate agent pipelines and report generation.

### 2.7 Performance & Resource Constraints

- The repo and README do not define explicit latency targets or upper bounds on LLM token usage.  
- There is no explicit backpressure or queue management when multiple users or multiple heavy queries are issued.

---

## 3. Recommended Next Steps

To strengthen the spec-driven development loop:

1. **Refine Requirements**  
   - Review and validate FR/NFR lists with stakeholders or maintainers.  
   - Promote key open questions (auth, SLAs, MindSpider integration) into explicit FRs when decisions are made.

2. **Extend Traceability**  
   - For each new feature or bugfix, link commit/PR descriptions to FR/NFR IDs.  
   - As more tests are added, annotate which FRs they cover.

3. **Address High-Impact Gaps First**  
   - Strengthen config validation (to avoid runtime surprises).  
   - Extend tests around ReportEngine and the agent pipelines.  
   - Add minimal auth or deployment guidance for users wanting to expose the system on a network.

This document should be updated as requirements evolve and as the codebase acquires more explicit contracts and tests.
