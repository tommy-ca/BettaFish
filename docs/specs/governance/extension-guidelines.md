# Extension Guidelines

## Adding a New Agent
1. **Proposal:** Draft ADR describing purpose, inputs/outputs, SLAs, and tooling.
2. **Specification:** Extend `requirements` (functional + non-functional) and update `architecture/component-design.md` with new nodes.
3. **Implementation:**
   - Create LangGraph StateGraph with planning/execution/validation pattern.
   - Register workflow entrypoint and update routing heuristics.
   - Define telemetry + dashboards before rollout.
4. **Validation:** Run integration tests with synthetic and historical workloads; capture metrics in traceability table.

## Adding a New Tool Adapter
- Implement `BettaFishTool` subclass with strict schema validation and cost metadata.
- Update Unified Tool catalog JSON consumed by router.
- Add contract tests using mocked upstream API responses.
- Document rate limits, quotas, and fallback plan.

## Extending APIs
- Update `interfaces/api-specification.md` and generate OpenAPI diffs.
- Provide versioned endpoints when making breaking changes; support minimum two minor versions in parallel.
- Ensure SDKs and Streamlit clients adopt new endpoints before deprecating old ones.

## Data Model Changes
- All schema modifications require migration scripts, backfill plan, and rollback strategy.
- Update `interfaces/data-models.md` diagrams and TypeScript/ Python models.
- Validate with canary data sets before promoting.

## Governance & Approvals
- Major extensions require Architecture Review Board (ARB) sign-off (meets Thursdays 09:00 PT).
- Security review mandatory for agents/tools that touch PII or new external APIs.
- Localization review needed if output surfaces to end users.

## Acceptance Criteria
- Extensions ship with updated specs, tests, telemetry, and runbooks.
- Routing accuracy remains ≥95% after deploying new agents/tools.
- Zero Sev1 incidents attributed to undocumented extensions.
