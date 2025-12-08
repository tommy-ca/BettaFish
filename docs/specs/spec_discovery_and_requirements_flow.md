# Spec-Driven Development: Repo Exploration & Requirements

This document defines how we explore the BettaFish repo and extract specifications/requirements in a **spec-driven development (SDD)** flow. It is intended to be a living document that guides future work and is updated as the codebase evolves.

---

## 1. Introduction & Scope

- **Goal**: Build and maintain an up-to-date specification of the system, driven by the existing code and tests, and use it to guide future changes.
- **Scope**: The entire BettaFish repository, including:
  - Engines: `InsightEngine`, `MediaEngine`, `QueryEngine`, `ReportEngine`, `ForumEngine`.
  - Crawling and topic systems: `MindSpider`.
  - Sentiment models: `SentimentAnalysisModel`.
  - UI and apps: `SingleEngineApp`, web app in `app.py` and related interfaces.
  - Shared utilities and scripts: `utils`, `tests`, deployment config.
- **Outcome**: A structured set of specs and requirements under `docs/specs/` that can be referenced when designing and implementing changes.

---

## 2. SDD Flow Overview

We use the following high-level spec-driven development flow for this repo:

1. **Discover & Map**  
   Explore the code, docs, and configs to understand the system, components, and interactions.

2. **Extract & Structure Specs**  
   Turn understanding into structured specs: system overview, component map, interfaces, and behavioral expectations.

3. **Derive Requirements (FRs/NFRs)**  
   From the specs, derive explicit functional and non-functional requirements, grouped by feature/engine.

4. **Trace Implementation ↔ Requirements**  
   Map requirements back to modules/classes/files to maintain traceability and identify gaps.

5. **Guide Changes via Specs**  
   For new features or refactors, first update/add specs & requirements, then implement code to satisfy them.

6. **Continuously Refine**  
   As code changes, keep specs and requirements updated so they remain a reliable source of truth.

The sections below break down how we execute this flow in this repo.

---

## 3. Phase 1 – High-Level Recon (Discover & Map)

**Objective**: Understand the overall purpose, architecture, and deployment model.

**Activities**:

- Read top-level docs:
  - `README.md`
  - `README-EN.md` (if present)
  - Any other root-level docs relevant to architecture or usage.
- Inspect entrypoints and runtime configuration:
  - `app.py` – main web app wiring (framework, routes, orchestrated engines).
  - `docker-compose.yml`, `Dockerfile`, `.env.example` – services, ports, environment variables, external dependencies.
  - `requirements.txt` (root and any module-specific ones) – key 3rd-party dependencies.

**Deliverable** (to be stored in a dedicated doc, e.g. `docs/specs/system_overview.md`):

- System purpose and key user-facing capabilities.
- Main components and how they are deployed.
- High-level data flow and dependency overview.

---

## 4. Phase 2 – Component & Module Map

**Objective**: Build a clear map of major components, their responsibilities, and interactions.

**Activities**:

For each top-level engine (`InsightEngine`, `MediaEngine`, `QueryEngine`, `ReportEngine`, `ForumEngine`):

- Inspect package root and agent:
  - `__init__.py`, `agent.py` – agent abstraction, how the engine is invoked, what it returns.
- LLM abstraction:
  - `llms/base.py`, `llms/__init__.py` – LLM interface, configuration, supported models/providers.
- Pipeline nodes:
  - `nodes/base_node.py`, `search_node.py`, `summary_node.py`, `formatting_node.py`, `report_structure_node.py`, etc.  
    Capture: pipeline stages, their inputs/outputs, chaining, and error-handling behavior.
- State management:
  - `state/state.py` – how state is represented, passed, and possibly persisted.
- Tools and utilities:
  - `tools/*` – external APIs, data sources, specialized logic (e.g., keyword optimizer, sentiment analyzer).
  - `utils/*` – shared helpers, DB access (`InsightEngine/utils/db.py`), text processing, etc.

For `ReportEngine`:

- Focus on report generation:
  - `nodes/html_generation_node.py`, `nodes/template_selection_node.py` – report workflow and template selection.
  - `report_template/*.md` – template structure, placeholders, and required sections.

For `MindSpider`:

- Topic extraction and news scraping:
  - `MindSpider/main.py`, `MindSpider/BroadTopicExtraction/*`, `MindSpider/config.py.example` – data sources, scheduling, batch/cron assumptions.
- Data model & DB:
  - `MindSpider/schema/db_manager.py`, `init_database.py`, `mindspider_tables.sql`, `models_bigdata.py`, `models_sa.py` – schema, key tables, relationships.
- Deep sentiment crawling:
  - `MindSpider/DeepSentimentCrawling/*`, `platform_crawler.py`, `MediaCrawler/*` – crawl orchestration, deduplication, backoff, robustness.

For `SentimentAnalysisModel`:

- Sentiment and topic models:
  - For each subdirectory (e.g. `WeiboSentiment_Finetuned`, `WeiboMultilingualSentiment`, `BertTopicDetection_Finetuned`, `WeiboSentiment_MachineLearning`, `WeiboSentiment_SmallQwen`):  
    - Read `README.md`, `predict*.py`, training scripts (`*_train.py`) to capture inputs/outputs, label spaces, languages, and serving assumptions.

For `SingleEngineApp`:

- Streamlit apps:
  - `SingleEngineApp/insight_engine_streamlit_app.py`
  - `SingleEngineApp/media_engine_streamlit_app.py`
  - `SingleEngineApp/query_engine_streamlit_app.py`  
  Capture: UI flows, input parameters, constraints (e.g., maximum query length, required fields).

For shared utilities:

- `utils/forum_reader.py`, `utils/github_issues.py`, `utils/retry_helper.py` – external data sources, retry/backoff patterns, error handling.

**Deliverable** (to be stored in e.g. `docs/specs/component_map.md`):

- Component-by-component map with responsibilities, key entrypoints, and dependencies.

---

## 5. Phase 3 – Interfaces & Integration Points

**Objective**: Document external interfaces and integration points (APIs, CLIs, storage, external services).

**Activities**:

- HTTP / Web interfaces:
  - `app.py`
  - `ForumEngine/llm_host.py`
  - `ReportEngine/flask_interface.py`
  - Any other flask/fastapi-like modules  
  Capture: endpoints, HTTP methods, input parameters, response schemas, and any auth/streaming behavior.

- CLI / Script interfaces:
  - `MindSpider/main.py`
  - `tests/run_tests.py`
  - Any `if __name__ == "__main__":` entrypoints  
  Capture: command-line args, required env vars, side effects (DB writes, file outputs, remote calls).

- Data storage:
  - `InsightEngine/utils/db.py`
  - `MindSpider/schema/*`
  - Any other DB-related modules  
  Capture: DB type, connection config, key tables/collections, ID/timestamp/status conventions.

- External services:
  - Engine `tools/*`, LLM wrappers, external search APIs, social media APIs  
  Capture: required credentials, rate-limit handling, error-handling expectations.

**Deliverable** (e.g. `docs/specs/interfaces_and_integrations.md`):

- Summary of HTTP APIs, CLIs, data storage, and external services.

---

## 6. Phase 4 – Behaviour via Tests & Examples

**Objective**: Derive behavioral expectations from tests and examples.

**Activities**:

- Explore test suite:
  - `tests/README.md`
  - `tests/run_tests.py`
  - `tests/test_monitor.py`
  - `tests/forum_log_test_data.py`  
  Capture: expected behaviours for monitoring/ForumEngine, edge cases, error conditions.

- Search for additional tests/examples:
  - Any `*_test.py` across the repo.
  - Doctest-like examples in docstrings or rich comments.

**Deliverable** (e.g. `docs/specs/behavioral_expectations.md`):

- Documented typical flows, edge cases, invariants, and behaviours for key components.

---

## 7. Phase 5 – Extract Functional & Non-Functional Requirements

**Objective**: Turn observed behaviours and structures into explicit requirements.

**Activities**:

- Functional requirements (FRs), grouped by feature/engine:
  - For each engine (`InsightEngine`, `MediaEngine`, `QueryEngine`, `ReportEngine`, `ForumEngine`, `MindSpider`, `SentimentAnalysisModel`):  
    - Derive statements of the form: “The system shall …”  
      - Inputs: what data is accepted (e.g., queries, URLs, text).  
      - Processing: what transformations/analysis is performed.  
      - Outputs: responses, stored records, generated reports.
  - For cross-engine flows:  
    - Describe end-to-end scenarios (e.g. crawling → sentiment/topic modeling → periodic reports) and participating modules.

- Non-functional requirements (NFRs):
  - Performance: timeouts, batching, pagination, caching where applicable.
  - Reliability: retries (`utils/retry_helper.py`), logging, monitoring.
  - Scalability: multi-service setup from `docker-compose.yml`, ability to scale crawlers/LLM calls.
  - Security & privacy: API key handling, PII in logs, endpoint auth (or gaps).
  - Internationalization: multi-language handling through different models and text processing.

**Deliverable** (e.g. `docs/specs/requirements.md`):

- `FR-xx` and `NFR-xx` items, grouped logically by engine/feature.

---

## 8. Phase 6 – Traceability & Gaps

**Objective**: Maintain traceability between requirements and implementation, and highlight gaps.

**Activities**:

- Map requirements to implementation:
  - For each `FR-xx` / `NFR-xx`, list main modules/classes/files implementing it (e.g. `InsightEngine/agent.py`, `InsightEngine/nodes/search_node.py`).

- Identify gaps and inconsistencies:
  - Features mentioned in README/docs but not clearly implemented.
  - Code paths that appear incomplete, experimental, or dead.

- Prioritize:
  - Mark requirements as core vs nice-to-have based on prominence and usage.
  - Note technical debt hotspots that impact maintainability.

**Deliverable** (e.g. `docs/specs/traceability_and_gaps.md`):

- Traceability mapping plus list of gaps and open questions.

---

## 9. Phase 7 – Using Specs to Drive Development

**Objective**: Ensure future changes start from and update specs, not just code.

**Practices**:

- Before implementation:
  - Add or update relevant sections under `docs/specs/` (overview, component map, interfaces, requirements).
  - Introduce new `FR-xx`/`NFR-xx` entries or adjust existing ones as necessary.

- During implementation:
  - Keep code changes aligned with the documented requirements and flows.
  - If implementation deviates, update specs accordingly.

- After implementation:
  - Verify that tests and behaviour match the specs.  
  - Update traceability mappings.

**Primary Spec Structure Under `docs/specs/`** (suggested):

- `spec_discovery_and_requirements_flow.md` (this document)
- `system_overview.md`
- `component_map.md`
- `interfaces_and_integrations.md`
- `behavioral_expectations.md`
- `requirements.md`
- `traceability_and_gaps.md`

These documents collectively implement the spec-driven development flow for this repo.
