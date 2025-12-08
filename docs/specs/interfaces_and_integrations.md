# Interfaces & Integrations – BettaFish

This document catalogs the main external interfaces (HTTP APIs, CLIs) and integration points (databases, external services, models) for the BettaFish system.

---

## 1. HTTP / Web Interfaces

### 1.1 Flask Main App (`app.py`)

**Base**: `http://HOST:PORT` (default `http://localhost:5000`)

- `/`  
  - Method: `GET`  
  - Description: Serve main HTML UI (`templates/index.html`).

- `/api/status`  
  - Method: `GET`  
  - Description: Return status of all managed apps/processes.
  - Response (JSON):
    - `insight|media|query|forum`: `{ status: "running|starting|stopped", port: number, output_lines: number }`.

- `/api/start/<app_name>`  
  - Method: `GET`  
  - Path params: `app_name ∈ {insight, media, query, forum}`.  
  - Description:
    - For `insight|media|query`: spawn the corresponding Streamlit app via `subprocess.Popen`, wait for health check.
    - For `forum`: start ForumEngine monitoring (`ForumEngine.monitor.start_forum_monitoring`).
  - Response (JSON): `{ success: bool, message: string }`.

- `/api/stop/<app_name>`  
  - Method: `GET`  
  - Description: Stop specified app. For `insight|media|query`: terminate the Streamlit process. For `forum`: stop ForumEngine monitoring.
  - Response (JSON): `{ success: bool, message: string }`.

- `/api/output/<app_name>`  
  - Method: `GET`  
  - Description: Return current log output for a given app.
  - Response (JSON):
    - For `forum`: `{ success: bool, output: [string], total_lines: number }` (from `logs/forum.log`).
    - For others: `{ success: bool, output: [string] }` (from `logs/<app_name>.log`).

- `/api/test_log/<app_name>`  
  - Method: `GET`  
  - Description: Write a test log line for debugging logging/Socket.IO wiring.
  - Response (JSON): `{ success: bool, message: string }`.

- `/api/forum/start` / `/api/forum/stop`  
  - Method: `GET`  
  - Description: Explicitly start/stop ForumEngine monitoring via `ForumEngine.monitor.start_forum_monitoring/stop_forum_monitoring`.
  - Response (JSON): `{ success: bool, message: string }`.

- `/api/forum/log`  
  - Method: `GET`  
  - Description: Return raw and parsed `forum.log` content.
  - Response (JSON): `{ success: bool, log_lines: [string], parsed_messages: [{ type, sender, content, timestamp, source }], total_lines: number }`.

- `/api/search`  
  - Method: `POST`  
  - Request body (JSON): `{ "query": string }`.
  - Behavior:
    - Validates non-empty query.
    - Checks which apps (`insight|media|query`) are currently `running`.
    - For each running app, sends `POST http://localhost:<api_port>/api/search` where `api_port` ∈ `{8601, 8602, 8603}`.
    - Collects per-app results.
  - Response (JSON):
    - `{ success: bool, query: string, results: { insight?: any, media?: any, query?: any } }` where each value is the downstream app’s JSON response or an error wrapper.

- `/api/config`  
  - Methods:
    - `GET`: return selected configuration values (from Pydantic `settings`).
      - Response: `{ success: bool, config: { KEY: string, ... } }` for keys in `CONFIG_KEYS` (DB, per-engine API keys, base URLs, model names, search API keys).
    - `POST`: update values, persisted to `.env`.
      - Request body: `{ KEY: value, ... }` (keys filtered to `CONFIG_KEYS`).
      - Response: `{ success: bool, config: { ...updated values... } }`.

- `/api/system/status`  
  - Method: `GET`  
  - Description: Return overall system start state.
  - Response: `{ success: bool, started: bool, starting: bool }`.

- `/api/system/start`  
  - Method: `POST`  
  - Description: Start the "full system" (DB init, stop Forum, start Streamlit apps, restart Forum, init ReportEngine).
  - Response:
    - On success: `{ success: true, message: "系统启动成功", logs: [string] }`.
    - On failure: `{ success: false, message: string, logs: [string], errors: [string] }`.

- `/api/system/shutdown`  
  - Method: `POST`  
  - Description: Gracefully shut down the Flask server and all managed components by terminating Streamlit child processes and stopping ForumEngine, then exiting the main process asynchronously.  
  - Response (JSON): `{ success: bool, message: string, ports?: [string] }` (includes a list of target ports when available).

### 1.2 Socket.IO Events (Flask Main App)

- `connect` (server → client): on connection, server emits `status` with message.
- `request_status` (client → server): triggers server to emit `status_update` with current app statuses.
- `console_output` (server → client): streamed log lines for `insight|media|query|forum` apps.
- `forum_message` (server → client): structured forum messages from `forum.log`.

These events are used by the web UI to show live logs and forum conversation.

### 1.3 ReportEngine Flask Blueprint (`ReportEngine/flask_interface.py`)

Mounted under `/api/report` when available.

- `/api/report/status`  
  - Method: `GET`  
  - Description: Check ReportEngine initialization state and readiness of input files (three agent report directories + `logs/forum.log`).
  - Response (JSON):
    - `{ success: bool, initialized: bool, engines_ready: bool, files_found: [string], missing_files: [string], current_task?: {...} }`.

- `/api/report/generate`  
  - Method: `POST`  
  - Request body (JSON): `{ query?: string, custom_template?: string }`.
  - Behavior:
    - Ensures no currently running task.
    - Clears report log (`clear_report_log`).
    - Checks `engines_ready` via `check_engines_ready()`.
    - Spawns background thread to run `run_report_generation`, which:
      - Loads latest `.md` report files from `insight_engine_streamlit_reports`, `media_engine_streamlit_reports`, `query_engine_streamlit_reports` and `logs/forum.log`.
      - Invokes `ReportAgent.generate_report(...)` with the aggregated inputs.
  - Response: `{ success: bool, task_id: string, message: string, task: {...} }`.

- `/api/report/progress/<task_id>`  
  - Method: `GET`  
  - Description: Get progress of a specific report generation task.
  - Response: `{ success: bool, task: {...} }` (returns a completed stub if task is not found, to avoid 404s in normal polling flows).

- `/api/report/result/<task_id>`  
  - Method: `GET`  
  - Description: Return HTML content of a completed report.
  - Response: `text/html` body or JSON error.

- `/api/report/result/<task_id>/json`  
  - Method: `GET`  
  - Description: Return HTML plus task metadata as JSON.
  - Response: `{ success: bool, task: {...}, html_content: string }`.

- `/api/report/download/<task_id>`  
  - Method: `GET`  
  - Description: Download report HTML file as an attachment.
  - Response: `send_file(...)` with `text/html` and `Content-Disposition: attachment`.

- `/api/report/cancel/<task_id>`  
  - Method: `POST`  
  - Description: Cancel a running or pending report task.
  - Response: `{ success: bool, message | error: string }`.

- `/api/report/templates`  
  - Method: `GET`  
  - Description: List available report templates from `settings.TEMPLATE_DIR`.
  - Response: `{ success: bool, templates: [{ name, filename, description, size }], template_dir: string }`.

- `/api/report/log`  
  - Method: `GET`  
  - Description: Read `report.log` to inspect ReportEngine’s internal operations.

- `/api/report/log/clear`  
  - Method: `POST`  
  - Description: Clear `report.log`.

- `/api/report/export/pdf/<task_id>`  
  - Method: `GET`  
  - Description: Export a completed report (identified by `task_id`) to PDF using the saved Document IR; performs a PDF dependency check (Pango/WeasyPrint) and returns a `503` JSON error with guidance if dependencies are missing.  
  - Query params: `optimize` (optional, default `true`) to enable layout optimization.  
  - Response: `application/pdf` stream with `Content-Disposition: attachment`, or JSON error.

- `/api/report/export/pdf-from-ir`  
  - Method: `POST`  
  - Request body (JSON): `{ "document_ir": { ... }, "optimize"?: bool }`.  
  - Description: Render a provided Document IR JSON payload directly to PDF without referencing a stored task, subject to the same PDF dependency checks as above.  
  - Response: `application/pdf` or JSON error.

---

## 2. CLI / Script Interfaces

### 2.1 MindSpider (`MindSpider/main.py`)

The README documents typical CLI usage:

- Setup & initialization:
  - `python MindSpider/main.py --setup` – initialize DB and environment.
- Topic extraction and crawling:
  - `python MindSpider/main.py --broad-topic` – run broad topic extraction (news + keywords).
  - `python MindSpider/main.py --complete --date YYYY-MM-DD` – run full pipeline for a specific date.
  - `python MindSpider/main.py --broad-topic --date YYYY-MM-DD` – topic extraction only.
  - `python MindSpider/main.py --deep-sentiment --platforms xhs dy wb` – deep sentiment crawling for specified platforms.

These commands rely on `MindSpider/schema` for DB schema and `MindSpider/config.py` for platform/API configs.

### 2.2 Test Runner (`tests/run_tests.py`)

- `python tests/run_tests.py`  
  - Discovers all methods on `TestLogMonitor` in `tests/test_monitor.py` and runs them in-process.
  - Exits with code `0` on all pass, `1` otherwise.

### 2.3 Sentiment Model Scripts

- `SentimentAnalysisModel/WeiboMultilingualSentiment/predict.py` (example)
  - Loads or downloads `tabularisai/multilingual-sentiment-analysis` model.
  - Provides interactive CLI:
    - `python predict.py` → interactive prompt for text input, `q` to quit, `demo` to see multilingual examples.
  - Not directly wired into Flask; instead, wrapped by `InsightEngine.tools.sentiment_analyzer`.

- Additional sentiment model CLIs exist under:
  - `SentimentAnalysisModel/WeiboSentiment_Finetuned/*/predict.py`.
  - `SentimentAnalysisModel/WeiboSentiment_MachineLearning/predict.py`.

These are used for standalone model evaluation and likely for debugging/experimentation.

---

## 3. Data Storage & Persistence

### 3.1 Primary Database (InsightEngine / MindSpider)

- Connection managed via `InsightEngine/utils/db.py`:
  - Builds URL from `settings.DB_DIALECT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
  - Uses SQLAlchemy 2 async engine with either `postgresql+asyncpg` or `mysql+aiomysql`.
  - Provides `fetch_all(query, params)` for read-only queries returning `List[Dict[str, Any]]`.
- MindSpider schema defined under `MindSpider/schema/`:
  - `mindspider_tables.sql` – core relational schema.
  - `db_manager.py`, `init_database.py`, `models_bigdata.py`, `models_sa.py` – DB initialization and ORM models.
- `app.py` triggers `MindSpider.main.MindSpider().initialize_database()` during system start, ensuring DB schema is present.

### 3.2 File-Based Artifacts

- Logs:
  - `logs/insight.log`, `logs/media.log`, `logs/query.log` – per-engine logs for Streamlit apps.
  - `logs/forum.log` – forum conversation log managed by `ForumEngine.monitor.LogMonitor`.
  - `logs/report.log`, `logs/report_baseline.json` – ReportEngine logs and file count baselines.
  - Additional logs may be written via `loguru` across modules.

- Reports & State:
  - Final reports: written by `ReportAgent` to `settings.OUTPUT_DIR` (mapped to `final_reports/` via Docker), filenames like `final_report_<query>_<timestamp>.html`.
  - Intermediate engine reports: `.md` files written by Streamlit apps to:
    - `insight_engine_streamlit_reports/`
    - `media_engine_streamlit_reports/`
    - `query_engine_streamlit_reports/`
  - Report state snapshots: `report_state_<query>_<timestamp>.json` under `final_reports/` (or configured `OUTPUT_DIR`).
  - QueryEngine and InsightEngine also save `.md` reports and `state_*.json` to their own `OUTPUT_DIR` directories.

---

## 4. Hatchet & LangGraph Orchestration (New)

### 4.1 Hatchet Workflows
The new architecture introduces durable execution workflows managed by Hatchet.

*   **Service Name**: `bettafish-worker` (The Python worker process connecting to Hatchet).
*   **Workflow**: `bettafish-analysis-workflow`
    *   **Input**: `{ "query": str, "mode": "deep" | "fast" }`
    *   **Trigger**:
        *   Manual: via CLI or API.
        *   Scheduled: via `bettafish-cron-workflow`.
    *   **Steps**:
        1.  `run_analysis`: Invokes the compiled LangGraph application.
        2.  `persist_results`: Saves the final `ForumState` to Postgres.

### 4.2 Internal Graph Transitions
The `ForumState` object is the contract between internal nodes.

*   **Supervisor -> Agent**: Passes `messages` (history) and `user_query`.
*   **Agent -> Supervisor**: Returns `AgentOutput` (summary + data).
    *   `QueryAgentNode`: Returns search summaries + source URLs.
    *   `MediaAgentNode`: Returns social sentiment + crawled stats.
    *   `InsightAgentNode`: Returns internal DB records.

---

## 5. External Services & APIs

### 5.1 LLM Providers (OpenAI-Compatible)

All engines use OpenAI-compatible chat completion APIs via provider-specific base URLs:

- Config keys (from `config.py` / `.env` and Pydantic `settings`):
  - `INSIGHT_ENGINE_API_KEY`, `INSIGHT_ENGINE_BASE_URL`, `INSIGHT_ENGINE_MODEL_NAME`.
  - `MEDIA_ENGINE_API_KEY`, `MEDIA_ENGINE_BASE_URL`, `MEDIA_ENGINE_MODEL_NAME`.
  - `QUERY_ENGINE_API_KEY`, `QUERY_ENGINE_BASE_URL`, `QUERY_ENGINE_MODEL_NAME`.
  - `REPORT_ENGINE_API_KEY`, `REPORT_ENGINE_BASE_URL`, `REPORT_ENGINE_MODEL_NAME`.
  - `FORUM_HOST_API_KEY`, `FORUM_HOST_BASE_URL`, `FORUM_HOST_MODEL_NAME`.

- Implementation examples:
  - ReportEngine: `ReportEngine/llms/LLMClient` used by `ReportAgent`.
  - QueryEngine: `QueryEngine/llms/LLMClient` used by `DeepSearchAgent`.
  - MediaEngine / InsightEngine: similar `LLMClient` wrappers.
  - ForumEngine host: `ForumEngine/llm_host.ForumHost` using `OpenAI(api_key=..., base_url=...)` to call `client.chat.completions.create`.

### 5.2 Web & Multimodal Search APIs (QueryEngine / MediaEngine)

- `QueryEngine/tools.TavilyNewsAgency`:
  - Wraps Tavily-like news search for multiple tools:
    - `basic_search_news`, `deep_search_news`, `search_news_last_24_hours`, `search_news_last_week`, `search_images_for_news`, `search_news_by_date`.
  - Uses `settings.TAVILY_API_KEY` and optional provider-specific parameters.

- These calls occur inside `QueryEngine.agent.DeepSearchAgent.execute_search_tool`, which maps tool names to specific API calls and normalizes responses into internal `TavilyResponse` objects.

- `MediaEngine/tools.BochaMultimodalSearch`:
  - Provides Bocha-based multimodal and web search for tools such as:
    - `comprehensive_search`, `web_search_only`, `search_for_structured_data`, `search_last_24_hours`, `search_last_week`.
  - Uses `settings.BOCHA_API_KEY` (or `settings.BOCHA_WEB_SEARCH_API_KEY` as a fallback) for authentication.

- These calls occur inside `MediaEngine.agent.DeepSearchAgent.execute_search_tool`, which normalizes `BochaResponse.webpages` into the common search-result schema used by the MediaEngine pipeline.

### 5.3 Media Crawling & DB APIs (InsightEngine / MindSpider)

- `InsightEngine.tools.MediaCrawlerDB`:
  - Local DB abstraction over crawled media and comments.
  - Query tools: `search_hot_content`, `search_topic_globally`, `search_topic_by_date`, `get_comments_for_topic`, `search_topic_on_platform`.
  - Returns `DBResponse` objects with fields like `title_or_content`, `platform`, `author_nickname`, `url`, `publish_time`, `engagement`.

- `MindSpider` external integrations:
  - Use Playwright (`playwright install chromium`) to crawl web and social platforms.
  - Platform-specific crawlers live under `MindSpider/DeepSentimentCrawling/MediaCrawler` and `platform_crawler.py`.
  - Platform coverage includes Weibo, Xiaohongshu, Douyin, Kuaishou, etc. (per README and config examples).

### 5.4 Sentiment Analysis Models

- Integrated via `InsightEngine/tools/sentiment_analyzer.py` (not fully reproduced here but implied by README and imports):
  - Supports model types: `bert`, `multilingual`, `qwen`, etc.
  - Configuration snippet (from README):
    - `SENTIMENT_CONFIG = { 'model_type': 'multilingual', 'confidence_threshold': 0.8, 'batch_size': 32, 'max_sequence_length': 512 }`.

- Backed by `SentimentAnalysisModel` scripts:
  - `WeiboMultilingualSentiment` (Hugging Face `tabularisai/multilingual-sentiment-analysis`).
  - Fine-tuned BERT/GPT-2 models and small Qwen models.
  - Traditional ML models used for lower-resource scenarios.

### 5.5 Retry & Resilience

- `utils/retry_helper.py` (used in `ForumEngine/llm_host.py`) provides:
  - `with_graceful_retry(SEARCH_API_RETRY_CONFIG, ...)` decorator around API calls.
  - Standardized retry/backoff behavior for LLM and search API invocations.

---

## 6. Cross-Component Integration Flows

### 6.1 End-to-End Report Generation

1. User submits query via Flask UI (`/api/search` and UI controls).  
2. Main app ensures `insight|media|query` apps and ForumEngine are running.  
3. Streamlit apps generate `.md` reports and log their progress to `logs/*.log`.  
4. ForumEngine monitors logs, extracts summary JSON from `SummaryNode` outputs, and writes normalized forum messages to `logs/forum.log` (plus emits `forum_message` events).  
5. When the user triggers report generation via `/api/report/generate`, ReportEngine:
   - Uses `FileCountBaseline` to detect new `.md` files from each engine report directory.
   - Loads those reports and `forum.log` via `load_input_files`.
   - Calls `ReportAgent.generate_report` using LLM to select templates and generate multi-section HTML.
   - Saves final HTML and state files and returns task metadata via `/status` and `/progress` endpoints.

### 6.2 Forum Host Integration

1. `ForumEngine.monitor.LogMonitor` tracks agent summary outputs and writes them into `forum.log` with `[HH:MM:SS] [SOURCE] content` format.  
2. Once `agent_speeches_buffer` reaches 5 messages, `_trigger_host_speech()` calls `ForumEngine.llm_host.generate_host_speech`.  
3. `ForumHost` parses forum logs, builds a structured prompt, and calls the configured Qwen (or other) model.  
4. Host speech is written back into `forum.log` with `[HOST]` source, visible to the UI and potentially to agents (via `utils/forum_reader.py`).

---

## 7. Alignment with SDD Flow

This document corresponds to **Phase 3 – Interfaces & Integration Points** in `docs/specs/spec_discovery_and_requirements_flow.md` and will be used to:

- Derive interface-level functional requirements (e.g., FRs about `/api/system/start`, `/api/report/*`, forum streaming).  
- Support contract testing and backward-compatibility checks when modifying APIs.  
- Provide a reference when onboarding new integrations (additional LLM providers, new crawlers, or sentiment engines).