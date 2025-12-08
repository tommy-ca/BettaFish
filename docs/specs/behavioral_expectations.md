# Behavioral Expectations – BettaFish

This document captures key behavioral expectations of the system derived from the test suite and from the current engine/report/forum implementations. It is an initial snapshot intended to guide future development and testing.

---

## 1. ForumEngine Log Monitoring & Parsing

### 1.1 Target Log Line Detection

From `tests/test_monitor.py` and `ForumEngine/monitor.py`:

- `LogMonitor.is_target_log_line(line)` must:
  - Recognize **summary-related** log lines for:
    - `FirstSummaryNode` (first summaries).
    - `ReflectionSummaryNode` (reflection summaries).
    - Module paths including `InsightEngine.nodes.summary_node`, `MediaEngine.nodes.summary_node`, `QueryEngine.nodes.summary_node`.
    - Compatibility patterns like `nodes.summary_node` and marker text such as `正在生成首次段落总结`, `正在生成反思总结`.
  - Support both log formats:
    - Old format: `[HH:MM:SS] ...`.
    - New loguru format: `YYYY-MM-DD HH:mm:ss.SSS | LEVEL | ...`.
  - Exclude:
    - `ERROR` level lines (including those with `| ERROR |` or `| ERROR    |`).
    - Lines containing error keywords such as `JSON解析失败`, `JSON修复失败`, `Traceback`, `File "..."`.
    - Non-target nodes (e.g., `report_structure_node`, SearchNode logs).

### 1.2 JSON Extraction & Formatting

Behavior inferred from tests:

- `LogMonitor.is_json_start_line(line)`:
  - Returns `True` when line contains `清理后的输出: {`.
- `LogMonitor.is_json_end_line(line)`:
  - Only returns `True` for pure `"}"` or `"] }"` lines **without** timestamps or log prefixes.
  - Lines with timestamps must be cleaned before evaluation.

- `LogMonitor.extract_json_content(lines)`:
  - Handles both:
    - Single-line JSON: entire JSON content on one log line.
    - Multi-line JSON: JSON content split across multiple log lines with timestamps (old and new formats).
  - Strips leading timestamps in both formats before concatenating JSON fragments.
  - First attempts direct `json.loads`; on failure, attempts to “fix” malformed JSON (e.g., unescaped quotes) using `fix_json_string` before retrying.
  - When parsing succeeds, passes the resulting object to `format_json_content`.

- `LogMonitor.format_json_content(json_obj)`:
  - Prioritizes fields in order:
    - `updated_paragraph_latest_state` (reflection or updated summary).
    - `paragraph_latest_state` (first summary content).
  - If either is present, returns the raw string (preserving `\n` as actual newlines).
  - If neither is present, returns a stringified JSON: `清理后的输出: <pretty-printed JSON>`.

- `LogMonitor.fix_json_string(json_text)`:
  - If `json_text` is already valid JSON, returns unchanged.
  - Otherwise, uses a state-machine approach to escape unescaped quotes **inside string values** while preserving real closing quotes.
  - After transformation, must return a JSON-parsable string or `None`.

### 1.3 Content Value Filtering

- `LogMonitor.is_valuable_content(line)`:
  - Returns `True` if the line contains `清理后的输出` (these are summaries).
  - Returns `False` for:
    - Error/diagnostic phrases like `JSON解析失败`, `JSON修复失败`, `直接使用清理后的文本`, `JSON解析成功`, `成功生成`, `已更新段落`, `正在生成`, `开始处理`, `处理完成`, `已读取HOST发言`, `读取HOST发言失败`, `未找到HOST发言`, `调试输出`, `信息记录`.
    - Lines that become too short after timestamp removal (length < ~30 characters).

### 1.4 End-to-End JSON Capture Behavior

- `LogMonitor.process_lines_for_json(lines, app_name)` must:
  - Track per-app state:
    - `capturing_json[app_name]`: whether currently accumulating JSON lines.
    - `json_buffer[app_name]`: buffered lines for a JSON object.
    - `in_error_block[app_name]`: whether inside an `ERROR` block (skip everything until next `INFO`).
  - For each line:
    - Determine log level (`INFO`, `ERROR`, etc.) from loguru-style segments.
    - If `ERROR`: set `in_error_block=True`, clear JSON buffers, skip line.
    - If `INFO`: exit `in_error_block` and resume normal processing.
    - When `in_error_block` is `True`, ignore all JSON and content (and reset buffers).
    - Start capturing JSON only when:
      - `is_target_log_line(line)` is `True` (SummaryNode), and
      - `is_json_start_line(line)` is `True`.
    - For single-line JSON (line ends with `"}"` and braces match): parse immediately and emit formatted content.
    - For multi-line JSON: append subsequent lines until a cleaned closing `"}"` or `"] }"` is encountered, then parse and emit.
    - For “valuable” non-JSON SummaryNode content: extract node content via `extract_node_content`, clean tags with `_clean_content_tags`, and emit.
  - Ensure SearchNode outputs are never captured, even if they contain `清理后的输出` JSON; this is enforced via `is_target_log_line` patterns and tests like `test_filter_search_node_output*`.
  - Ensure SummaryNode error logs are never captured, even if they mention `nodes.summary_node`.

### 1.5 Forum Session Lifecycle

- `LogMonitor.monitor_logs()` behavior (as exercised implicitly by tests and app wiring):
  - On start:
    - Logs `ForumEngine: 论坛创建中...`.
    - Records baseline line counts and file positions for `insight.log`, `media.log`, `query.log`.
  - When the first `FirstSummaryNode` (or equivalent marker) is detected in any app:
    - Sets `is_searching=True` and resets `search_inactive_count`.
    - Calls `clear_forum_log()` to start a fresh session.
  - While `is_searching=True`:
    - Continuously reads new lines and passes them to `process_lines_for_json`.
    - Writes captured contents to `forum.log` with `[timestamp] [SOURCE] content` via `write_to_forum_log`.
    - Tracks whether logs grow (`any_growth`) or shrink (`any_shrink`).
    - If any log shrinks (e.g., application restart): ends the current forum session, writes `=== ForumEngine 论坛结束 - <timestamp> ===`, resets state, and waits for a new `FirstSummaryNode` trigger.
    - If there is no new content for a prolonged period (e.g., `search_inactive_count >= 7200` iterations): automatically ends the forum session and writes an end marker.

### 1.6 Host Speech Trigger

- `LogMonitor` maintains `agent_speeches_buffer` and `host_speech_threshold` (default 5).
- When buffer length reaches threshold, `_trigger_host_speech()`:
  - Calls `ForumEngine.llm_host.generate_host_speech(recent_speeches)` if `HOST_AVAILABLE` and `is_host_generating` is `False`.
  - On success, writes host speech to `forum.log` with source `HOST`, resets `is_host_generating`, and drops the processed speeches from buffer.
  - On failure, logs error and does not write partial content.

---

## 2. ReportEngine Behavior

From `ReportEngine/agent.py` and `ReportEngine/flask_interface.py`:

- `ReportAgent` must:
  - Initialize with proper logging and file baselines:
    - Use `FileCountBaseline` to record baseline counts for the three agent report directories.
    - Add a dedicated log sink writing to `settings.LOG_FILE`.
  - Template selection:
    - Prefer a user-provided `custom_template` when given.
    - Otherwise, call `TemplateSelectionNode.run(...)` with `{ query, reports, forum_logs }` and record the chosen template name and selection reasoning in state metadata.
    - On failure, fall back to a standard “社会公共热点事件分析报告” template.
  - Report construction and HTML generation:
    - Use nodes such as `TemplateSelectionNode`, `DocumentLayoutNode`, `WordBudgetNode`, and `ChapterGenerationNode` to build a validated Document IR from the three engine reports plus `forum.log`.
    - Use the HTML renderer (via `ReportAgent.generate_report`) to turn the IR into final HTML, then mark `ReportState` as completed and store HTML content.
  - Saving outputs:
    - Write HTML reports to `OUTPUT_DIR` with names `final_report_<query>_<timestamp>.html`.
    - Save state as `report_state_<query>_<timestamp>.json`, storing metadata like template name and generation time.

- `ReportAgent.check_input_files(...)` must:
  - Compare current counts of `.md` files in engine report directories against baselines.
  - Only report `ready=True` when **all three** engines have at least one new `.md` file since baseline and `forum.log` exists.
  - Return `files_found` and `missing_files` lists describing new file counts and missing inputs.

- `ReportAgent.load_input_files(file_paths)` must:
  - Read the latest `.md` file for each of `query`, `media`, `insight` into `reports` list (in that order), logging sizes.
  - Read `forum.log` into `forum_logs` if present.

- `ReportAgent.generate_report(...)` must:
  - Accept `reports` and `forum_logs` and run template selection + HTML generation.
  - Optionally save the report and state (when `save_report=True`).
  - Return at least `{ html_content, report_filepath?, report_relative_path?, state_filepath?, state_relative_path? }`.

- Flask endpoints (`/api/report/*`) must:
  - Enforce single active report task at a time (via `task_lock` and `current_task`).
  - Update `ReportTask` status milestones: `pending → running (10% → 30% → 50% → 90%) → completed` or `error` with messages.
  - Be robust to polling after task cleanup by returning a “completed” stub instead of hard 404s for `/progress/<task_id>`.

---

## 3. QueryEngine & InsightEngine Behavioral Patterns

From `QueryEngine/agent.py` and `InsightEngine/agent.py` (DeepSearchAgent variants):

- Both engines implement a similar **multi-step research pipeline**:
  1. **Report structure generation**: `ReportStructureNode` builds a list of paragraphs (title + content).
  2. **Per-paragraph loop**:
     - Generate an initial search query + tool choice (`FirstSearchNode.run`).
     - Execute search using appropriate tool wrapper:
       - QueryEngine: `TavilyNewsAgency` (web/news search).
       - InsightEngine: `MediaCrawlerDB` (local opinions DB).
       - In InsightEngine, search queries may be optimized by `keyword_optimizer` prior to issuing DB queries.
     - Normalize search results into a common schema and append to `paragraph.research` history.
     - Generate first summary (`FirstSummaryNode`), updating `paragraph.research.latest_summary`.
  3. **Reflection loop** (up to `MAX_REFLECTIONS`):
     - Generate reflection queries (`ReflectionNode`), including optional date ranges and platform filters.
     - Execute additional searches and update histories.
     - Generate refined summaries (`ReflectionSummaryNode`) using new results and previous summary.
  4. **Final report generation**: `ReportFormattingNode` formats all paragraph summaries into a final report; on failure, fallback manual formatting is used.

- Input validation and defaults:
  - Both agents validate date strings (`YYYY-MM-DD`) before using date-based search tools; invalid or missing dates cause a fallback to default search tools (`basic_search_news` or `search_topic_globally`).
  - Both engines enforce configured limits (`MAX_SEARCH_RESULTS_FOR_LLM`, per-tool limits) rather than trusting model-suggested limits.

- Result handling:
  - QueryEngine: logs counts and basic metadata for each search result (title, published date).
  - InsightEngine: deduplicates DB results (via `_deduplicate_results`) and may perform sentiment analysis on results when enabled.

---

## 4. Sentiment Analysis Behavior

From `InsightEngine/agent.py` and `SentimentAnalysisModel/WeiboMultilingualSentiment/predict.py`:

- For integrated sentiment analysis in InsightEngine:
  - Sentiment analyzer (`multilingual_sentiment_analyzer`) must:
    - Lazy-initialize models if not yet initialized and not disabled.
    - Handle failures gracefully by returning original text and marking `analysis_performed=False` but not breaking the main pipeline.
  - `DeepSearchAgent._perform_sentiment_analysis(results)`:
    - Converts search results into dictionaries with fields like `content`, `platform`, `author`, `url`, `publish_time`.
    - Calls `analyze_query_results` with `min_confidence` threshold (e.g., 0.5).
    - On success, attaches a `sentiment_analysis` object to `DBResponse.parameters`.
    - On failure, logs the error and returns `None` without raising.

- For standalone sentiment CLI (`WeiboMultilingualSentiment/predict.py`):
  - On first run, downloads HF model and saves to `./model`; on subsequent runs, reloads locally.
  - Presents an interactive REPL with:
    - `q` to quit.
    - `demo` to show multi-language examples.
  - For each text, prints main label (5-level: `非常负面`, `负面`, `中性`, `正面`, `非常正面`) and confidence, plus full probability distribution.

These behaviors inform expectations for model latency, robustness, and UX when integrated into InsightEngine.

---

## 5. Testing Behaviors & Invariants

The current `tests/test_monitor.py` suite encodes several invariants:

- Parsing functions must correctly handle both legacy `[HH:MM:SS]` and loguru `YYYY-MM-DD ... | LEVEL | ...` formats.
- Only summary nodes (First/Reflection) should feed the forum; SearchNode outputs, even when formatted similarly, must be filtered out.
- Error logs and tracebacks from SummaryNode must **not** appear in forum-derived content.
- Real-world log examples (for QueryEngine, InsightEngine, MediaEngine) must be parsed into human-readable content containing key phrases like company names and “核心发现/更新版/综合信息概览” without JSON field names leaking.

Future tests for other components (ReportEngine, agents, sentiment integration) should mirror this style by providing realistic sample data and asserting behavior at the boundary points (e.g., endpoints, node outputs, report files).

---

## 6. Alignment with SDD Flow

This document implements **Phase 4 – Behaviour via Tests & Examples** from `docs/specs/spec_discovery_and_requirements_flow.md` and will be used to:

- Drive future test design for new features by clarifying expected behavior at log, API, and report boundaries.
- Inform functional requirements about forum behavior, summary generation, and error handling.
- Provide concrete examples when debugging regressions in log parsing, forum orchestration, or report generation.
