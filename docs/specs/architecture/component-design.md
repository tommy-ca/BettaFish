# Component Design Specification

## Component Inventory

| Component | Responsibility | Technology | Key Interfaces |
|-----------|----------------|------------|----------------|
| `DBOS Workflow Orchestrator` | Durable request routing, task decomposition, progress tracking | DBOS Python workflows + steps | LangGraph Router, Agent Executors, State Store |
| `LangGraph Router` | Classify requests, choose agents, enforce policy | LangGraph StateGraph | DBOS Workflow, Agent Graphs |
| `InsightEngine StateGraph` | Database mining, sentiment pipeline, summarization | LangGraph + async DB clients | MindSpider DB, Tavily fallback |
| `QueryEngine StateGraph` | Real-time web search, ranking, dedupe | LangGraph + Tavily SDK | Tavily API, Unified Tool Interface |
| `MediaEngine StateGraph` | Multimodal search, embedding alignment | LangGraph + Bocha SDK | Bocha AI, Vision utilities |
| `ReportEngine StateGraph` | Multi-round reporting, templating, export | LangGraph + Renderer | Markdown->HTML/PDF Services |
| `ForumHost Event Bus` | Human-in-the-loop moderation and notifications | LangGraph node + WebSocket | Streamlit UIs, Moderation tools |
| `Unified Tool Interface` | Consistent adapter layer for external APIs | Async adapters + Pydantic contracts | Tavily, Bocha, DeepSeek, Gemini |
| `State & Data Layer` | Durable state, knowledge stores, audit logs | DBOS storage + Postgres + MinIO | All workflows |
| `Experience Layer` | Flask dashboard + Streamlit agent UIs | Flask, Streamlit | Operators, API clients |

## Detailed Component Specifications

### DBOS Workflow Orchestrator
- **Topology:** Router workflow → Coordinator workflow → Aggregator workflow, each a DBOS workflow composed of steps.
- **Durable State:** Every workflow stores `workflow_id`, `query`, `selected_agents`, `context`, and `event_log` records. State snapshots occur before and after each external call.
- **Concurrency Model:** Use `WorkflowHandle.map` for fan-out across agent executors with deterministic ordering for replay safety.
- **Timeouts & Retries:** Default 60 s per agent execution with exponential backoff (2, 4, 8 attempts). Hard deadline enforced at workflow level (5 min) with compensating actions to close open resources.
- **Interfaces:**
  - Input: `BettaFishRequest` (query, persona, constraints, attachments).
  - Output: `BettaFishResponse` (status, results[], citations[], artifacts[]).
- **Observability Hooks:** Emit `WorkflowEvent` to monitoring topic (see monitoring spec) at state transitions.

### LangGraph Router
- **Inputs:** sanitized query payload from DBOS.
- **Logic:**
  1. Embed query via `InsightEmbeddingTool`.
  2. Score against routing heuristics (search vs analysis vs report vs multimodal).
  3. Apply guardrails (e.g., compliance tags, blocked topics) before returning `selected_agents`.
- **Outputs:** `RoutingDecision` containing agents, required tools, SLA window, and confidence.
- **Extensibility:** Add new `RoutingRule` objects (Pydantic models) with priority, condition, action.

### Agent StateGraphs
Each agent follows a similar pattern:
1. **Input Node:** Validate payload, hydrate cached context.
2. **Planning Node:** Build task list and tool plan.
3. **Execution Nodes:** Parallelizable tasks using Unified Tool Interface.
4. **Quality Node:** Run validator (e.g., schema checks, toxicity filter).
5. **Output Node:** Persist result and emit events.

#### InsightEngine
- **Special Nodes:** `KeywordOptimizer`, `DatabaseMiner`, `SentimentAggregator`.
- **Storage:** Reads from MindSpider via async SQLAlchemy; caches in Redis cluster.
- **Constraints:** Batch DB fetches ≤500 rows, dedupe by URL hash.

#### QueryEngine
- **Special Nodes:** `WebSearch`, `ResultRanker`, `Verifier`.
- **Tools:** Tavily primary, SerpAPI fallback via shared interface.
- **Validation:** At least three high-confidence citations per answer.

#### MediaEngine
- **Special Nodes:** `MultimodalFetcher`, `EmbeddingAligner`, `NarrativeSynthesizer`.
- **Pipelines:** Handles Bocha payload fan-out for image, video, audio concurrently.

#### ReportEngine
- **Special Nodes:** `TemplateSelector`, `OutlineGenerator`, `IterativeAuthor`, `Formatter`.
- **Output:** Markdown + HTML + optionally PDF (via WeasyPrint) persisted to object storage with metadata for retrieval.

### ForumHost Event Bus
- Replaces ad-hoc file polling with LangGraph node subscribed to WebSocket feed.
- Maintains moderation queue with human acknowledgement requirement for sensitive flows.

### Unified Tool Interface
- Abstract base `BettaFishTool` ensures validation, telemetry, and retry policy.
- All adapters must expose `metadata` describing cost, limits, and supported modalities for routing decisions.

### State & Data Layer
- **Primary Store:** DBOS durable store backed by Postgres (high-availability cluster).
- **Artifact Store:** MinIO (S3-compatible) for attachments, reports, embeddings.
- **Cache Layer:** Redis for transient context and rate-limit tokens.

### Experience Layer
- Flask dashboard consumes DBOS APIs for workflow status and acts as admin gateway.
- Streamlit apps subscribe to ForumHost events for real-time updates and allow human corrections.

## Sequence Scenarios

### Standard Public Opinion Query
```
User → Flask API → DBOS Router → LangGraph Router
      → Agent Executors (Insight + Query) ↺ Unified Tools
      → Aggregator → Formatter → Response + Report artifact
```

### Crisis Monitoring Escalation
```
Sensor Event → DBOS Coordinator → Media + Insight agents (parallel)
            → Sentiment spike? → ForumHost moderation required
            → ReportEngine drafts crisis brief → PagerDuty alert
```

## Failure Handling
- **Agent Failure:** DBOS marks node as failed, dispatches retry to warm standby agent instance. If failure persists, router downgrades plan and notifies ForumHost.
- **External API Rate Limits:** Unified Tool Interface enforces token bucket; if exhausted, router is signaled to re-plan using cached data.
- **State Corruption:** Automatic rollback via DBOS ACID transactions; health checks verify schema migrations before activation.

## Acceptance Criteria
- All components expose health endpoints consumed by monitoring stack.
- Router decisions are reproducible for identical inputs (hash-based determinism).
- Agent graphs can be started/stopped independently with no cascading failures.
- ForumHost delivers human escalation events within 5 s.
- Unified Tool adapters log every external request with correlation IDs.
