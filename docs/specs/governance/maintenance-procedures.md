# Maintenance Procedures

## Release Management
- **Weekly Release:** Cut branch `release/<YYYY-MM-DD>` from `main`, run smoke tests, tag `vX.Y.Z` after sign-off.
- **Hotfix Flow:** Tag `hotfix/<issue>` from latest production tag, apply fix, cherry-pick back to `main` and active release branch.

## Environment Hygiene
- **Dependency Updates:** Run `pip-compile --upgrade` bi-weekly; create tracking issue for breaking changes.
- **Database Migrations:** Apply via DBOS migration workflow with canary databases before production.
- **Secrets Rotation:** Rotate API keys every 90 days; document rotation windows and owners.

## Monitoring & Alerts
- PagerDuty schedule ensures 24/7 coverage; on-call responds within 15 minutes.
- Triage playbooks stored under `runbooks/` cover top 10 failure modes (Tavily outage, DB pressure, Streamlit crash, etc.).
- All Sev1 incidents trigger postmortem within 48 hours with actionable follow-ups.

## Backup & Restore
- Postgres: snapshot hourly, retain 14 days, test restore weekly.
- Object storage: replicate to secondary region nightly; verify checksums.
- Config store: export encrypted blob to secure bucket with 30-day retention.

## Compliance & Auditing
- Quarterly access reviews for all secrets and admin consoles.
- Maintain audit trail for workflow executions and human interventions (ForumHost).
- Keep SBOM up to date using `cyclonedx` after every release.

## Acceptance Criteria
- No release goes live without successful rollback test in staging.
- Incident response metrics: MTTA < 10 min, MTTR < 60 min for Sev1.
- Backup restoration tested and logged every week.
