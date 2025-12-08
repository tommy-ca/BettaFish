# Component Map – BettaFish

This document maps the major components of the BettaFish system to their responsibilities, key modules, and relationships. It focuses on the engines/agents and primary subsystems described in the repository.

---

## 1. Overview of Major Components

- **Flask Main App** (`app.py`)
- **QueryEngine** (`QueryEngine/`)
- **MediaEngine** (`MediaEngine/`)
- **InsightEngine** (`InsightEngine/`)
- **ReportEngine** (`ReportEngine/`)
- **ForumEngine** (`ForumEngine/`)
- **MindSpider** (`MindSpider/`)
- **SentimentAnalysisModel** (`SentimentAnalysisModel/`)
- **SingleEngineApp** (`SingleEngineApp/`)
- **Shared Utilities & Tests** (`utils/`, `tests/`)

---

## 2. Flask Main App (`app.py`)

**Role**: Central orchestrator and web UI backend.

- **Key Responsibilities**:
  - Serve the main web UI via Flask and Socket.IO.
  - Manage lifecycle of the three Streamlit apps (Insight, Media, Query): start/stop, health checks, logs.
  - Initialize and register ReportEngine’s HTTP interface (if available) as a Flask blueprint under `/api/report`.
  - Initialize MindSpider and ensure the database schema is ready (via `MindSpider.main.MindSpider`).
  - Initialize and control ForumEngine monitoring.
  - Provide APIs for:
    - Agent status (`/api/status`).
    - Starting/stopping individual apps (`/api/start/<app_name>`, `/api/stop/<app_name>`).
    - Unified search (`/api/search`) that fans out queries to running agent APIs.
    - Accessing logs and forum messages.
    - Reading/updating configuration via `.env` (`/api/config`).
    - System-level start (`/api/system/start`) and status (`/api/system/status`).
- **Notable Modules & Data Structures**:
  - `CONFIG_KEYS`, `read_config_values`, `write_config_values` – integration with `config.py` and `.env` via Pydantic settings.
  - `processes` dict – tracks Streamlit app and ForumEngine status, ports, and logs.
  - `STREAMLIT_SCRIPTS` – maps logical app names to `SingleEngineApp/*.py` scripts.
  - `MindSpider` usage – ensures database initialization before the overall system starts.

---

## 3. QueryEngine (`QueryEngine/`)

**Purpose**: Broad web and news search agent.

- **Key Files & Directories**:
  - `QueryEngine/agent.py` – `DeepSearchAgent` orchestration implementing a multi-step news/web research pipeline (report structure → search → reflection → summarization).
  - `QueryEngine/llms/` – LLM abstraction layer for query-related reasoning.
    - `base.py` – base LLM client (OpenAI-compatible).
  - `QueryEngine/nodes/` – pipeline nodes for processing queries:
    - `base_node.py` – base node abstraction.
    - `search_node.py` – executes web/news searches.
    - `summary_node.py` – summarizes search results.
    - `formatting_node.py` – formats data for downstream consumption.
    - `report_structure_node.py` – structures outputs for report integration.
  - `QueryEngine/prompts/` – prompt templates.
  - `QueryEngine/utils/text_processing.py` – shared text processing utilities.
  - `QueryEngine/tools/` – Tavily-based search integration (`TavilyNewsAgency`, `TavilyResponse`) and helpers used by `DeepSearchAgent.execute_search_tool`.
- **Responsibilities**:
  - Interpret user query in context of global web/news search.
  - Perform multi-step web search (API-based or headless browser-based) with configured limits.
  - Aggregate and summarize results into a structured representation for the forum and ReportEngine.

---

## 4. MediaEngine (`MediaEngine/`)

**Purpose**: Multimodal (text + media) content analysis agent.

- **Key Files & Directories** (confirmed from current implementation):
  - `MediaEngine/agent.py` – main `DeepSearchAgent` orchestration using `BochaMultimodalSearch` for multimodal/web search.
  - `MediaEngine/llms/` – LLM abstraction for multimodal reasoning.
  - `MediaEngine/nodes/` – pipeline nodes, analogous to other engines:
    - `base_node.py`, `search_node.py`, `summary_node.py`, `formatting_node.py`, `report_structure_node.py`.
  - `MediaEngine/prompts/` – prompts tailored for multimodal understanding.
  - `MediaEngine/utils/text_processing.py` – text and possibly media metadata processing.
  - `MediaEngine/tools/` – Bocha-based multimodal search integration and helpers.
- **Responsibilities**:
  - Use Bocha multimodal/web search to retrieve media-rich and textual content relevant to the topic.
  - Extract and interpret multi-modal signals (e.g., video captions, comments, engagement metrics).
  - Summarize media-derived insights for integration with other agents.

---

## 5. InsightEngine (`InsightEngine/`)

**Purpose**: Private / internal data mining and deep opinion analysis.

- **Key Files & Directories**:
  - `InsightEngine/agent.py` – core agent logic for orchestrating search, sentiment, and summarization over private data.
  - `InsightEngine/llms/base.py` – LLM wrapper implementing a unified OpenAI-compatible client.
  - `InsightEngine/nodes/`:
    - `base_node.py` – common node base class.
    - `search_node.py` – queries internal DB / data sources.
    - `summary_node.py` – summarizes retrieved records.
    - `formatting_node.py` – prepares structured outputs.
    - `report_structure_node.py` – organizes insights into report sections.
  - `InsightEngine/tools/`:
    - `keyword_optimizer.py` – Qwen-based middleware for optimizing search keywords.
    - `search.py` – DB query tools over internal opinion data.
    - `sentiment_analyzer.py` – integration with SentimentAnalysisModel and configuration for different sentiment engines.
  - `InsightEngine/state/state.py` – state definitions for agent runs.
  - `InsightEngine/prompts/prompts.py` – prompt templates for private DB analysis.
  - `InsightEngine/utils/`:
    - `db.py` – DB connection and basic operations.
    - `text_processing.py` – internal text cleaning/normalization utilities.
- **Responsibilities**:
  - Connect to configured internal databases (business DBs or MindSpider’s opinion DB).
  - Optimize search queries via keyword optimization.
  - Retrieve, filter, and aggregate relevant records.
  - Perform sentiment/stance analysis using pluggable models.
  - Produce structured insights to feed the forum and ReportEngine.

---

## 6. ReportEngine (`ReportEngine/`)

**Purpose**: Multi-round report generation and formatting.

- **Key Files & Directories**:
  - `ReportEngine/agent.py` – `ReportAgent` orchestration (template selection → layout → word budget → chapter generation → IR composition → rendering and persistence).
  - `ReportEngine/llms/` – LLM interface for drafting and refining report sections.
  - `ReportEngine/nodes/`:
    - `base_node.py` – base node class.
    - `template_selection_node.py` – selects appropriate report template based on context.
    - `document_layout_node.py` – designs document title, TOC, hero section, and visual theme.
    - `word_budget_node.py` – plans per-chapter word budgets and global writing guidelines.
    - `chapter_generation_node.py` – generates and validates chapter-level JSON content.
  - `ReportEngine/core/` – template parsing, chapter storage, and document IR stitching (`template_parser.py`, `chapter_storage.py`, `stitcher.py`).
  - `ReportEngine/ir/` – IR schema and validator for chapter JSON and document structure.
  - `ReportEngine/renderers/` – HTML/PDF renderers and chart utilities.
  - `ReportEngine/state/` – `ReportState` models and helpers.
  - `ReportEngine/utils/` – configuration, dependency checks, JSON helpers, and chart validation/repair utilities.
  - `ReportEngine/report_template/` – library of report templates for different scenarios:
    - `企业品牌声誉分析报告模板.md`
    - `市场竞争格局舆情分析报告模板.md`
    - `日常或定期舆情监测报告模板.md`
    - `特定政策或行业动态舆情分析报告.md`
    - `社会公共热点事件分析报告模板.md`
    - (and others)
  - `ReportEngine/flask_interface.py` – exposes ReportEngine as a Flask blueprint, registering endpoints (report generation, progress, streaming logs, downloads, and PDF export) consumed by the main app.
- **Responsibilities**:
  - Collect consolidated analysis outputs from all agents and the forum.
  - Choose the best-fitting template based on query type and context.
  - Orchestrate multiple LLM calls to design layout, plan word budgets, draft, refine, and validate each report chapter, composing them into a Document IR.
  - Render the IR into final HTML (and optionally PDF) and store artifacts under `final_reports/` and IR output directories.

---

## 7. ForumEngine (`ForumEngine/`)

**Purpose**: Multi-agent forum monitor and coordinator.

- **Key Files**:
  - `ForumEngine/monitor.py` – main monitoring logic:
    - `start_forum_monitoring`, `stop_forum_monitoring` used by `app.py`.
    - Watches agent logs and writes forum messages to `logs/forum.log`.
  - `ForumEngine/llm_host.py` – LLM-based forum host/moderator:
    - Summarizes agent exchanges.
    - Provides guidance for the next analysis round.
- **Responsibilities**:
  - Maintain a centralized "forum" view of agent reasoning.
  - Filter, parse, and enrich log entries into structured forum messages.
  - Provide real-time updates to the front-end via Socket.IO (`forum_message` events).
  - Ensure the debate loop between agents is coherent and productive.

---

## 8. MindSpider (`MindSpider/`)

**Purpose**: Crawling, topic extraction, and deep sentiment crawling system.

- **Key Files & Directories**:
  - `MindSpider/main.py` – CLI entrypoint orchestrating setup, broad-topic extraction, and deep sentiment crawling (`--setup`, `--broad-topic`, `--complete`, `--deep-sentiment`, etc.).
  - `MindSpider/config.py.example` – example configuration for sources, DB, and crawling behavior.
  - `MindSpider/BroadTopicExtraction/`:
    - `database_manager.py` – manages DB interactions for topic data.
    - `get_today_news.py` – fetches current news.
    - `main.py` – main script for topic extraction.
    - `topic_extractor.py` – core topic extraction logic.
  - `MindSpider/DeepSentimentCrawling/`:
    - `keyword_manager.py` – manages crawling keywords.
    - `main.py` – deep crawling orchestration.
    - `MediaCrawler/` – platform-specific crawler implementations.
    - `platform_crawler.py` – orchestrates crawling across different platforms.
  - `MindSpider/schema/`:
    - `db_manager.py` – DB management (connection, migrations).
    - `init_database.py` – initializes schema.
    - `mindspider_tables.sql` – SQL definition for core tables.
    - `models_bigdata.py`, `models_sa.py` – ORM / data models for large-scale and sentiment analysis data.
- **Responsibilities**:
  - Populate and maintain the opinion database from social platforms.
  - Provide topic and sentiment signals that can be consumed by InsightEngine and others.
  - Support scheduled or ad-hoc crawling workflows.

---

## 9. SentimentAnalysisModel (`SentimentAnalysisModel/`)

**Purpose**: Collection of sentiment analysis models and training scripts.

- **Key Subdirectories**:
  - `BertTopicDetection_Finetuned/` – fine-tuned BERT topic detection:
    - `dataset/`, `train.py`, `predict.py`, etc.
  - `WeiboMultilingualSentiment/` – multilingual sentiment analysis:
    - `predict.py`, `README.md` describing inputs/outputs and supported languages.
  - `WeiboSentiment_Finetuned/` – fine-tuned Chinese models:
    - `BertChinese-Lora/` – BERT + LoRA fine-tuning.
    - `GPT2-AdapterTuning/` – GPT-2 with adapters.
    - `GPT2-Lora/` – GPT-2 with LoRA.
  - `WeiboSentiment_MachineLearning/` – traditional ML models:
    - `base_model.py`, `bayes_train.py`, `bert_train.py`, `lstm_train.py`, `svm_train.py`, `xgboost_train.py`, etc.
    - `model/` – serialized model binaries.
    - `data/stopwords.txt` – preprocessing resources.
  - `WeiboSentiment_SmallQwen/` – small Qwen-based fine-tuned models.
- **Responsibilities**:
  - Provide reusable sentiment prediction scripts (`predict.py`, `predict_universal.py`).
  - Serve as backends for `InsightEngine/tools/sentiment_analyzer.py` and related tooling.
  - Enable experimentation with different modeling approaches.

---

## 10. SingleEngineApp (`SingleEngineApp/`)

**Purpose**: Streamlit-based UIs for running each engine independently.

- **Key Files**:
  - `SingleEngineApp/query_engine_streamlit_app.py`
  - `SingleEngineApp/media_engine_streamlit_app.py`
  - `SingleEngineApp/insight_engine_streamlit_app.py`
- **Responsibilities**:
  - Provide quick, focused interfaces for:
    - Submitting queries to each engine.
    - Viewing intermediate and final results.
  - Expose HTTP APIs (e.g., `/api/search`) that `app.py` calls on ports `8601/8602/8603` during unified searches.

---

## 11. Shared Utilities & Tests

### 11.1 Shared Utilities (`utils/`)

- `utils/forum_reader.py`
  - Provides helper functions for agents to read and interpret forum logs.
- `utils/github_issues.py`
  - Integrates with GitHub issues (likely for bug/feature management or as a data source).
- `utils/retry_helper.py`
  - Encapsulates retry logic for network requests, including backoff and error handling.

### 11.2 Tests (`tests/`)

- `tests/run_tests.py`
  - Central entrypoint for running tests.
- `tests/test_monitor.py`
  - Tests ForumEngine’s monitoring behavior against sample logs.
- `tests/test_report_engine_sanitization.py`
  - Tests ReportEngine’s handling and sanitization of generated content.
- `tests/forum_log_test_data.py`
  - Provides synthetic forum log data for testing parser behavior.
- `tests/README.md`
  - Explains how to run tests and what is covered.

---

## 12. Relationships Between Components

- **Main App ↔ Engines**:
  - `app.py` spawns and manages Streamlit processes for Insight/Media/Query.
  - Communicates with them via HTTP APIs (e.g., `/api/search`) on dedicated ports.
- **Main App ↔ ForumEngine**:
  - `app.py` starts/stops ForumEngine monitoring.
  - A background thread (`monitor_forum_log`) reads `logs/forum.log` and pushes structured messages to clients.
- **Main App ↔ ReportEngine**:
  - Registers `ReportEngine.flask_interface.report_bp` under `/api/report`.
  - Relies on `initialize_report_engine` to prepare the report agent.
- **Engines ↔ MindSpider / DB**:
  - InsightEngine uses `InsightEngine/utils/db.py` and MindSpider’s schema to query stored opinion data.
- **Engines ↔ SentimentAnalysisModel**:
  - `InsightEngine/tools/sentiment_analyzer.py` and similar tools call into sentiment model scripts or services.
- **User Interfaces**:
  - Flask front-end (`templates/index.html`, static assets) provides a unified dashboard.
  - Streamlit apps provide per-engine UIs.

---

## 13. Next Steps for Specs

This component map provides a structural view and will be refined as we inspect each engine in more detail. In the spec-driven development flow, this document will support:

- Mapping functional requirements (FR-xx) to specific components.
- Identifying which modules participate in each end-to-end scenario.
- Highlighting technical debt or missing tests per component.
