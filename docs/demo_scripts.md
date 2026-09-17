# AI Data Trust Platform — Demo Scripts

> Practical demo playbook for presenting the project in a portfolio review, interview, or local technical walkthrough.

This document is intentionally operational. It does not try to repeat the whole architecture or every implementation detail. Its job is to answer one question:

> **If someone gives me 5–20 minutes to demonstrate the platform, what should I run, show, and explain?**

The scripts below are written for the current project architecture:

- Streamlit UI
- FastAPI
- SQL Server
- Apache Airflow
- Prometheus
- Grafana
- Raw/Bronze persistence
- Dataset Catalog and Versioning
- Data Contracts
- Validation Gate
- Governance
- Lifecycle and Promotion
- Lineage
- Data Quality and Trust Score
- Anomaly / Drift / Privacy
- Freshness / Volume monitoring
- Operational Events
- Rule-grounded AI Assistant

---

# 1. Demo philosophy

Do not try to click every page.

A strong demo should tell one coherent story:

```text
Data arrives
    ↓
The platform records where it came from
    ↓
The platform identifies the dataset/version
    ↓
A Data Contract may validate its schema
    ↓
Quality / privacy / trust evidence is generated
    ↓
Validation and Governance decide what is allowed
    ↓
Lifecycle prevents unsafe promotion
    ↓
Airflow operationalizes the workflow
    ↓
Freshness and Volume monitors watch the dataset later
    ↓
Operational Events record incidents
    ↓
Observability shows current platform state
    ↓
The AI Assistant explains existing evidence
```

The main message is:

> **The project is not only a data-quality dashboard. It models the lifecycle of trusted data from ingestion to governed use and operational monitoring.**

---

# 2. Recommended demo modes

## 2.1. Five-minute quick demo

Use this when the interviewer only wants a short portfolio overview.

Show:

1. Docker services are healthy.
2. Streamlit Upload Dataset page.
3. Governed workflow result.
4. Dataset lifecycle and lineage.
5. Airflow DAGs.
6. Observability Overview.
7. AI Assistant.

Do not spend time opening every analytical page.

---

## 2.2. Ten-to-fifteen-minute interview demo

Recommended default.

Show:

1. Platform startup and health.
2. Dataset ingestion and provenance.
3. Catalog + versioning.
4. Data Contract Gate.
5. Validation Gate.
6. Governance Decision.
7. Lifecycle / Promotion.
8. End-to-end Lineage.
9. Airflow pipeline history.
10. Freshness and Volume monitoring.
11. Observability Overview.
12. AI Assistant.

Optionally show Trust Score, Privacy or Drift if the interviewer asks about analytics/ML.

---

## 2.3. Deep technical demo

Use only when the interviewer wants implementation detail.

In addition to the normal flow, show:

- SQL Server persistence.
- API endpoints.
- Data Contract versioning.
- Pipeline run persistence.
- Operational Event idempotency.
- Freshness / Volume policy history.
- Prometheus metrics.
- Grafana.
- GitHub Actions.
- Tests and linting.

---

# 3. Pre-demo checklist

Run this before presenting the project.

```powershell
git status

docker compose ps -a
```

Expected Git state for a normal demo:

```text
On branch main
nothing to commit, working tree clean
```

If working on a feature branch, that is also fine, but know which branch you are presenting.

Check that the environment file exists:

```powershell
Test-Path .env
```

Never print secrets during a demo.

Check that the sample Airflow dataset exists if you plan to trigger the main DAG:

```powershell
Test-Path data\lifecycle_test\v3\sample_customers.csv
```

The Airflow DAG uses the container-side default:

```text
/app/data/lifecycle_test/v3/sample_customers.csv
```

If the local sample is unavailable, use another prepared dataset and provide its path through Airflow DAG parameters.

---

# 4. Start the core platform

Build and start the normal platform services:

```powershell
docker compose up -d --build
```

Check status:

```powershell
docker compose ps -a
```

The main services are expected to include:

```text
sqlserver
bootstrap
api
ui
prometheus
grafana
```

The `bootstrap` container is expected to exit successfully after applying database bootstrap/migrations.

---

# 5. Start Airflow

Airflow belongs to the `orchestration` Compose profile.

Build it when the source or Airflow image has changed:

```powershell
docker compose --profile orchestration build airflow
```

Start Airflow:

```powershell
docker compose --profile orchestration up -d airflow
```

Check status:

```powershell
docker compose --profile orchestration ps -a
```

Check DAG discovery:

```powershell
docker compose exec airflow airflow dags list
```

The project currently includes operational DAGs such as:

```text
ai_data_trust_pipeline
ai_data_trust_smoke
data_freshness_monitor
data_volume_monitor
```

The main governed pipeline is manually triggered.

Freshness and Volume monitors are scheduled every five minutes.

---

# 6. Local URLs

Use these during the demo.

| Component | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| FastAPI | `http://localhost:8000` |
| FastAPI Swagger | `http://localhost:8000/docs` |
| Airflow | `http://localhost:8080` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

---

# 7. Platform health check

Before opening the UI, prove that the backend is alive.

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/health" |
    ConvertTo-Json -Depth 10
```

Then check readiness:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/ready" |
    ConvertTo-Json -Depth 10
```

The difference matters:

```text
/health
    -> Is the API process alive?

/ready
    -> Is the API ready to serve the application,
       including its SQL Server dependency?
```

Show the API feature registry:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/info" |
    ConvertTo-Json -Depth 10
```

Talking point:

> The backend exposes health/readiness separately, and SQL Server is part of readiness rather than simple liveness.

---

# 8. Main UI demo — Upload Dataset

Open:

```text
http://localhost:8501
```

Go to:

```text
Upload Dataset
```

Upload a prepared CSV, Excel or JSON file.

The page performs or displays much more than a simple file preview.

Explain the sequence:

```text
File upload
    ↓
Raw/Bronze ingestion
    ↓
SHA-256 provenance
    ↓
Catalog registration
    ↓
Dataset version
    ↓
Data Contract Gate
    ↓
Validation Gate
    ↓
Governance Decision
    ↓
Lifecycle synchronization
```

---

# 9. Show ingestion provenance

On the Upload Dataset page, point out:

- ingestion ID
- SHA-256
- raw byte size
- source type
- Raw/Bronze path

Talking point:

> The original artifact is preserved instead of immediately overwriting a downstream table. SHA-256 gives the platform content-based provenance.

If Streamlit reruns with the same uploaded dataset in the current session, the page avoids creating a new ingestion merely because Streamlit rerendered.

This is a useful implementation detail to mention because Streamlit reruns can otherwise accidentally cause duplicate side effects.

---

# 10. Show Catalog and Versioning

Point out:

- `catalog_id`
- dataset version number
- whether the version is NEW or EXISTING
- ingestion event ID

Core idea:

```text
same logical dataset
+ same SHA-256
= reuse known version

same logical dataset
+ different SHA-256
= create a new version
```

Also open, if useful:

- dataset version history
- ingestion history

Talking point:

> Ingestion history and dataset versions are different concepts. The same version can be ingested more than once without inventing a new data version.

---

# 11. Data Contract demo

Open:

```text
Data Contracts
```

The page can display:

- active contract
- contract history
- enforcement mode
- schema rules
- inactive versions
- contract activation
- creation of a new contract version

The contract model supports column rules such as:

```text
column_name
expected_type
is_required
is_nullable
```

Supported expected types include:

```text
NUMERIC
CATEGORICAL
DATETIME
BOOLEAN
TEXT
```

Enforcement modes:

```text
BLOCK
WARN
```

Explain the difference:

```text
BLOCK
    -> a breaking contract can stop the governed workflow

WARN
    -> the breaking contract is recorded,
       but the workflow may continue
```

Strong interview talking point:

> A Data Contract is versioned and only one version is active for a catalog at a time. Contract enforcement therefore becomes reproducible governance evidence, not a hard-coded UI check.

---

# 12. Validation Gate demo

Return to the governed Upload Dataset workflow.

Show:

- validation status
- High / Medium / Low issue counts
- blocking issue count
- validation artifact
- validation history

Current policy behavior exposed by the UI:

```text
High severity
    -> blocks the dataset

Medium / Low
    -> recorded as evidence
       but do not block by themselves
```

Typical lifecycle result:

```text
ACCEPTED
    -> validated artifact / Silver candidate

REJECTED
    -> quarantine
```

Talking point:

> Data arriving is not the same as data being trusted.

---

# 13. Governance Decision demo

Show the Governance section.

Possible decisions include:

```text
APPROVED
REVIEW_REQUIRED
REJECTED
```

Explain:

> Governance consumes evidence from the workflow. It is deliberately separate from the numerical Trust Score.

A useful distinction to say aloud:

```text
Trust Score
    = evidence summary

Governance Decision
    = policy decision
```

A high score does not automatically bypass blocking governance conditions.

---

# 14. Lifecycle and Promotion demo

Show the dataset lifecycle.

Current lifecycle states include:

```text
NEW
VALIDATED
QUARANTINED
ACTIVE
SUPERSEDED
```

Explain the normal positive path:

```text
NEW
    ↓
VALIDATED
    ↓
Governance APPROVED
    ↓
manual promotion
    ↓
ACTIVE
```

If a newer version is promoted:

```text
old ACTIVE
    ↓
SUPERSEDED
```

If validation fails:

```text
NEW
    ↓
QUARANTINED
```

The important design choice:

> Promotion is deliberate. Ingestion does not automatically make a dataset ACTIVE.

If the displayed version is promotion-eligible, use the UI promotion button.

If it is already ACTIVE, do not force a state change just for the demo.

---

# 15. Lineage demo

Expand:

```text
End-to-end Dataset Lineage
```

Show:

- ingestion events
- contract validations
- validation history
- governance decisions
- lifecycle events
- current state
- Raw/Bronze artifact
- latest validation artifact

Conceptual lineage:

```text
Raw/Bronze
    ↓
Data Contract
    ↓
Validation
    ↓
Governance
    ↓
Lifecycle
    ↓
ACTIVE / SUPERSEDED / QUARANTINED
```

Talking point:

> The lineage is not only file provenance. It includes decision evidence explaining why a specific version reached its current lifecycle state.

---

# 16. Optional API lineage demo

If you already know a real `version_id`, run:

```powershell
$versionId = 1

Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/datasets/$versionId/lineage" |
    ConvertTo-Json -Depth 20
```

Do not hard-code `1` during an interview unless it is actually valid in your current database.

Use the version ID shown by the UI.

---

# 17. Optional API promotion demo

Only run this when the version is genuinely eligible for promotion.

```powershell
$versionId = 1

Invoke-RestMethod `
    -Method POST `
    -Uri "http://localhost:8000/api/datasets/$versionId/promote" |
    ConvertTo-Json -Depth 10
```

Expected behavior is governance-aware.

A non-eligible version should not be promoted merely because the API endpoint was called.

---

# 18. Data Profile demo

Open:

```text
Data Profile
```

Show:

- total rows / columns
- missing cells
- duplicate rows
- schema summary
- numeric statistics
- categorical statistics
- data preview

Keep this short.

This page explains the data, but it is not the strongest platform differentiator.

---

# 19. Quality Issues demo

Open:

```text
Quality Issues
```

Show:

- issue groups
- severity
- affected columns
- recommendations
- missing-value checks
- duplicate checks
- type checks
- range checks
- categorical checks

Talking point:

> Quality issues are converted into structured evidence that can later influence scoring, validation and governance.

---

# 20. Trust Score demo

Open:

```text
Trust Score
```

Show:

- overall score
- risk level
- AI readiness
- score breakdown
- weighted contribution
- anomaly evidence

Also show:

```text
Save full scan to SQL Server
```

A saved scan persists:

- dataset metadata
- scan run
- Trust Score
- quality issues

Talking point:

> The score engine is a shared core implementation. FastAPI and Streamlit should not maintain competing scoring formulas.

---

# 21. Anomaly Detection demo

Open:

```text
Anomaly Detection
```

The project currently demonstrates:

```text
IQR
Z-score
Isolation Forest
```

Show:

- total anomaly rows
- anomaly rate
- anomaly score
- per-method results

Do not claim that anomaly detection automatically proves that a row is invalid.

Say:

> Anomaly detection creates investigation evidence. Business validity still depends on context.

---

# 22. Drift demo

Open:

```text
Drift Analysis
```

Prepare:

- a baseline dataset
- a current dataset

The current implementation demonstrates:

- schema drift
- PSI
- KS-test
- categorical distribution drift
- distribution-difference visualizations

Explain:

> Drift asks whether current data still resembles the baseline. It is different from row-level quality validation.

---

# 23. Privacy Risk demo

Open:

```text
Privacy Risk
```

The current rule-based scanner can identify patterns such as:

- email
- phone
- citizen ID
- name/address heuristics

Show:

- Privacy Safety Score
- risk level
- PII columns
- PII cell rate
- findings

Do not present the scanner as a legal compliance engine.

Say:

> It is a rule-based privacy risk signal used as governance evidence.

---

# 24. Report demo

Open:

```text
Reports
```

Show that the platform can build an HTML report from available session evidence.

A fuller report may include:

- profile
- quality
- Trust Score
- privacy
- drift

The page can also show persisted scan history from SQL Server.

---

# 25. Main Airflow pipeline demo

The main DAG is:

```text
ai_data_trust_pipeline
```

It is manually triggered.

Confirm the default sample exists inside the Airflow container:

```powershell
docker compose exec airflow sh -c `
    'ls -l /app/data/lifecycle_test/v3/sample_customers.csv'
```

Trigger the DAG:

```powershell
docker compose exec airflow `
    airflow dags trigger ai_data_trust_pipeline
```

Wait briefly:

```powershell
Start-Sleep -Seconds 15
```

Inspect recent runs:

```powershell
docker compose exec airflow `
    airflow dags list-runs ai_data_trust_pipeline
```

The newest run should eventually be:

```text
success
```

Talking point:

> Airflow does not duplicate the business logic. It orchestrates the same platform workflow and persists operational run state.

---

# 26. Pipeline Operations demo

Open:

```text
Pipeline Operations
```

Show:

- run history
- run status
- source path
- duration
- catalog/version references
- validation status
- governance decision
- lifecycle state
- failure details when present

Important clarification:

> Historical FAILED runs do not mean the latest pipeline is currently failing.

Always distinguish:

```text
historical failure count
```

from:

```text
latest pipeline state
```

---

# 27. Pipeline Runs API demo

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/pipeline-runs?limit=20" |
    ConvertTo-Json -Depth 10
```

If you have a real run ID:

```powershell
$pipelineRunId = 1

Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/pipeline-runs/$pipelineRunId" |
    ConvertTo-Json -Depth 10
```

---

# 28. Freshness Monitoring demo

Open:

```text
Dataset Freshness
```

The monitor uses a policy with:

```text
max_age_minutes
is_enabled
```

Possible latest statuses include:

```text
FRESH
STALE
NO_DATA
```

The Airflow DAG is:

```text
data_freshness_monitor
```

Its schedule is:

```text
*/5 * * * *
```

which means every five minutes.

Make sure the DAG is active:

```powershell
docker compose exec airflow `
    airflow dags unpause -y data_freshness_monitor
```

If Airflow replies:

```text
No paused DAGs were found
```

that is fine; it means there was nothing to unpause.

Show recent runs:

```powershell
docker compose exec airflow `
    airflow dags list-runs data_freshness_monitor
```

Talking point:

> Freshness history may continue to record checks while operational alerts are designed not to spam the same incident repeatedly.

---

# 29. Freshness API demo

Read policy:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/freshness/catalog/1/policy" |
    ConvertTo-Json -Depth 10
```

Read history:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/freshness/catalog/1/history?limit=10" |
    ConvertTo-Json -Depth 10
```

Run a manual check:

```powershell
Invoke-RestMethod `
    -Method POST `
    -Uri "http://localhost:8000/api/freshness/catalog/1/check" |
    ConvertTo-Json -Depth 10
```

Replace catalog ID `1` if your demo database uses another catalog.

---

# 30. Volume Monitoring demo

Open:

```text
Dataset Volume
```

The policy contains:

```text
drop_threshold_pct
spike_threshold_pct
is_enabled
```

Possible statuses:

```text
NORMAL
DROP
SPIKE
NO_BASELINE
```

The Airflow DAG is:

```text
data_volume_monitor
```

Its schedule is also every five minutes:

```text
*/5 * * * *
```

Activate it if necessary:

```powershell
docker compose exec airflow `
    airflow dags unpause -y data_volume_monitor
```

Inspect runs:

```powershell
docker compose exec airflow `
    airflow dags list-runs data_volume_monitor
```

---

# 31. Volume API demo

Read policy:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/volume/catalog/1/policy" |
    ConvertTo-Json -Depth 10
```

Read history:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/volume/catalog/1/history?limit=10" |
    ConvertTo-Json -Depth 10
```

Run a manual check:

```powershell
Invoke-RestMethod `
    -Method POST `
    -Uri "http://localhost:8000/api/volume/catalog/1/check" |
    ConvertTo-Json -Depth 10
```

A `NORMAL` check should not produce a breach alert.

A `DROP` or `SPIKE` may produce a `DATASET_VOLUME_BREACH` operational event.

---

# 32. Idempotency talking point

Freshness/Volume monitoring is a good place to explain idempotency.

The intended operational behavior is:

```text
same logical check/event
    ↓
do not create uncontrolled duplicate alerts
```

This matters because scheduled systems run repeatedly.

A monitor that creates a new alert every five minutes for the same incident would quickly become noisy and operationally useless.

---

# 33. Operational Events demo

API:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/operational-events?limit=50" |
    ConvertTo-Json -Depth 10
```

Operational Events can connect incidents to platform context through fields such as:

- event type
- severity
- source
- stage
- catalog ID
- version ID
- pipeline run ID
- reference ID
- detail JSON

Talking point:

> Operational Events are a reusable event layer. Freshness, Volume and pipeline operations can surface incidents without each feature inventing a separate alert model.

---

# 34. Observability Overview demo

Open:

```text
Data Observability Overview
```

This is one of the strongest final demo pages because it combines:

- monitored datasets
- Freshness policies and latest status
- Volume policies and latest status
- latest pipeline status
- recent operational events
- recent failed pipeline history

API equivalent:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/observability/overview" |
    ConvertTo-Json -Depth 10
```

Important distinction:

```text
Freshness / Volume breach count
    -> based on latest persisted monitor state

recent failed pipeline run count
    -> historical count inside the loaded run window
```

Therefore:

```text
3 historical failed runs
```

does not imply:

```text
the latest pipeline is failed
```

---

# 35. Prometheus demo

Open:

```text
http://localhost:9090
```

The API exposes metrics at:

```text
http://localhost:8000/metrics
```

Quick PowerShell check:

```powershell
Invoke-WebRequest `
    -Uri "http://localhost:8000/metrics" |
    Select-Object -ExpandProperty Content
```

Explain two design details:

1. Route labels use route templates instead of raw IDs where possible.
2. Health/readiness/metrics probe traffic is excluded from normal HTTP business metrics.

Why this matters:

> It avoids unnecessary metric cardinality and prevents infrastructure probes from distorting application traffic statistics.

---

# 36. Grafana demo

Open:

```text
http://localhost:3000
```

Grafana reads Prometheus metrics through provisioned configuration.

Use Grafana to demonstrate:

- API request activity
- latency
- status codes
- operational service behavior

Do not spend too long here unless the role is observability/platform focused.

---

# 37. AI Assistant demo

Open:

```text
AI Assistant
```

Before asking questions, make sure the current Streamlit session already contains relevant scan results.

Useful demo questions:

```text
Tóm tắt dataset hiện tại
Giải thích Data Trust Score
Nhóm nào đang kéo điểm xuống nhiều nhất?
Nếu chỉ sửa 3 vấn đề thì nên sửa gì?
Đánh giá privacy risk
Phân tích anomaly/outlier
Phân tích drift detection
Giải thích AI readiness
```

The key design principle:

```text
Rule-grounded assistant
```

The assistant is intended to explain supplied platform evidence.

It should not invent facts about the dataset that are not present in the current context.

Talking point:

> I deliberately started with a grounded assistant rather than attaching an unconstrained LLM to the platform. That keeps explanations traceable to actual scan evidence and gives a safer base for later AI upgrades.

---

# 38. AI Assistant API demo

Check assistant status:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/assistant/status" |
    ConvertTo-Json -Depth 10
```

A direct `/ask` request requires both:

```text
question
context
```

The backend does not independently query arbitrary hidden dataset state.

That is part of the grounding model.

---

# 39. Data Contract API demo

Read contract history:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/data-contracts/catalog/1" |
    ConvertTo-Json -Depth 20
```

Read active contract:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/data-contracts/catalog/1/active" |
    ConvertTo-Json -Depth 20
```

Use the UI to create contract versions during a live demo unless you already prepared a valid JSON payload.

This avoids wasting interview time typing schema definitions.

---

# 40. Scan History API demo

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/scans/history?limit=20" |
    ConvertTo-Json -Depth 10
```

Latest scan:

```powershell
Invoke-RestMethod `
    -Method GET `
    -Uri "http://localhost:8000/api/scans/latest" |
    ConvertTo-Json -Depth 20
```

Talking point:

> Analytical scan history and governed dataset lifecycle are related but not identical concepts. The project persists both operational/platform evidence and analytical scan evidence.

---

# 41. Optional direct governed workflow API demo

The governed workflow endpoint is:

```text
POST /api/workflows/run
```

It accepts a file upload.

Using `curl.exe` from PowerShell is convenient:

```powershell
curl.exe `
    -X POST `
    -F "file=@data\lifecycle_test\v3\sample_customers.csv" `
    "http://localhost:8000/api/workflows/run"
```

Only run this when the local file exists.

The response can include:

- ingestion ID
- catalog ID
- version ID
- version number
- Validation result
- Governance result
- Trust Score
- Privacy status
- lifecycle state
- promotion eligibility
- Data Contract evidence
- lineage URL

Important:

> The governed workflow deliberately does not automatically promote the result to ACTIVE.

---

# 42. GitHub Actions demo

Open the repository Actions page.

The CI pipeline runs:

```text
Ruff
pytest
compileall
```

Local equivalents:

```powershell
ruff check .

python -m pytest -q

python -m compileall `
    api `
    src `
    database `
    app `
    orchestration

git diff --check
```

Talking point:

> Features are validated locally and again in GitHub Actions before being merged.

---

# 43. Recommended ten-minute speaking script

A concise narrative can sound like this:

### Minute 0–1 — Architecture

> This project is an AI-assisted Data Trust Platform. Data enters through ingestion, receives content-based provenance, is cataloged and versioned, evaluated against quality and governance evidence, and only then becomes eligible for promotion.

### Minute 1–3 — Governed workflow

Upload a dataset and show:

```text
ingestion
catalog/version
contract
validation
governance
lifecycle
```

Say:

> Ingestion does not mean trusted. The workflow separates arrival from approval.

### Minute 3–4 — Lineage

Open end-to-end lineage.

Say:

> For a version I can trace ingestion, contract validation, quality validation, governance and lifecycle transitions.

### Minute 4–5 — Airflow

Open Airflow.

Show:

```text
ai_data_trust_pipeline
data_freshness_monitor
data_volume_monitor
```

Say:

> The core logic is reusable. Airflow schedules or orchestrates it rather than owning a second implementation.

### Minute 5–7 — Observability

Open Freshness, Volume and Observability Overview.

Say:

> After data becomes part of the platform, I continue monitoring whether it is arriving on time and whether row volume changes unexpectedly.

### Minute 7–8 — Operational history

Open Pipeline Operations / Operational Events.

Say:

> Failed runs and monitor breaches are persisted so the platform has operational history instead of only UI notifications.

### Minute 8–9 — AI

Open AI Assistant.

Say:

> The assistant is rule-grounded. It explains evidence already produced by the platform instead of making unsupported claims.

### Minute 9–10 — Engineering quality

Briefly show:

```text
Docker Compose
Prometheus / Grafana
GitHub Actions
tests
```

Finish with:

> The main goal was to build a coherent platform prototype, not just collect disconnected tools.

---

# 44. What not to do during a demo

Avoid these mistakes.

## Do not reset the database immediately before presenting

Historical pipeline runs, monitor checks, lineage and operational events make the project look more realistic.

## Do not trigger destructive or unpredictable changes unnecessarily

If the current state already demonstrates ACTIVE lifecycle, Freshness, Volume and pipeline history, use it.

## Do not demo every page

Too many pages make the project look like disconnected features.

Tell one end-to-end story.

## Do not claim production readiness

A good description is:

```text
portfolio-grade / engineering prototype
```

not:

```text
production-ready enterprise platform
```

## Do not call the AI Assistant a general-purpose LLM

The current assistant is intentionally rule-grounded.

## Do not hide historical failures

Explain them.

A persisted failed pipeline run is evidence that the platform tracks failures, not automatically evidence that the project is currently broken.

---

# 45. Useful troubleshooting commands

## API logs

```powershell
docker compose logs --tail 100 api
```

## UI logs

```powershell
docker compose logs --tail 100 ui
```

## SQL Server logs

```powershell
docker compose logs --tail 100 sqlserver
```

## Airflow logs / status

```powershell
docker compose --profile orchestration ps -a

docker compose logs --tail 150 airflow
```

## Rebuild API after backend changes

```powershell
docker compose build api

docker compose up -d api
```

## Rebuild UI after Streamlit changes

```powershell
docker compose build ui

docker compose up -d ui
```

## Rebuild Airflow after Python/core image changes

```powershell
docker compose --profile orchestration build airflow

docker compose --profile orchestration up -d airflow
```

---

# 46. SQL Server quick verification

Run a harmless connectivity query:

```powershell
@'
SELECT
    DB_NAME() AS database_name,
    SYSUTCDATETIME() AS checked_at;
GO
'@ | docker compose exec -T sqlserver sh -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d AIDataTrustPlatform -W'
```

Do not print the actual database password.

---

# 47. Freshness history verification

Example:

```powershell
@'
SELECT TOP 10
    freshness_check_id,
    catalog_id,
    ingestion_event_id,
    version_id,
    max_age_minutes,
    age_minutes,
    freshness_status,
    checked_at
FROM dbo.dataset_freshness_history
ORDER BY
    freshness_check_id DESC;
GO
'@ | docker compose exec -T sqlserver sh -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d AIDataTrustPlatform -W'
```

Use this only when deeper database verification is useful.

---

# 48. Volume history verification

```powershell
@'
SELECT TOP 10
    volume_check_id,
    catalog_id,
    ingestion_event_id,
    baseline_row_count,
    current_row_count,
    row_change_pct,
    volume_status,
    checked_at
FROM dbo.dataset_volume_history
ORDER BY
    volume_check_id DESC;
GO
'@ | docker compose exec -T sqlserver sh -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d AIDataTrustPlatform -W'
```

---

# 49. Operational Events verification

```powershell
@'
SELECT TOP 20
    operational_event_id,
    event_key,
    event_type,
    severity,
    event_source,
    event_stage,
    catalog_id,
    version_id,
    pipeline_run_id,
    reference_id,
    occurred_at
FROM dbo.operational_events
ORDER BY
    operational_event_id DESC;
GO
'@ | docker compose exec -T sqlserver sh -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d AIDataTrustPlatform -W'
```

---

# 50. Final local validation before a showcase commit

Run:

```powershell
ruff check .

python -m pytest -q

python -m compileall `
    api `
    src `
    database `
    app `
    orchestration

git diff --check

git status --short
```

Do not hard-code a test count in documentation.

The test suite will continue growing.

The meaningful statement is:

```text
all current tests pass
```

---

# 51. Recommended screenshots for GitHub / CV portfolio

When the project is stable, capture:

1. Streamlit Upload Dataset — governed workflow result.
2. Dataset Lifecycle / Lineage.
3. Data Contract Management.
4. Trust Score.
5. Airflow DAG list with successful runs.
6. Dataset Freshness.
7. Dataset Volume.
8. Data Observability Overview.
9. Grafana dashboard.
10. GitHub Actions green CI.
11. AI Assistant grounded answer.

Do not put all screenshots in the README.

A small curated set is stronger than a wall of images.

---

# 52. Suggested interviewer questions and short answers

## “Why SQL Server?”

> I wanted a real relational persistence layer for catalog/version history, governance evidence, monitoring history and operational runs rather than keeping everything in Streamlit session state.

## “Why Airflow if the workflow already exists in Python?”

> Airflow is the orchestration layer. The domain workflow remains reusable Python logic, so the scheduler does not become the business-logic source of truth.

## “Why Data Contracts and Validation Gate separately?”

> The contract checks expected schema/interface compatibility. The Validation Gate evaluates data-quality evidence and blocking rules. They solve different problems.

## “Why Governance after validation?”

> Passing technical validation does not necessarily mean the dataset is approved for use. Governance combines additional policy evidence such as Trust Score and privacy risk.

## “Why manual promotion?”

> It explicitly separates data arrival from trusted activation and preserves governance control.

## “Why Freshness and Volume?”

> Quality at ingestion is not enough. Once a dataset is operational, the platform also needs to know whether data stopped arriving or changed size unexpectedly.

## “Why rule-grounded AI?”

> I wanted explanations tied to concrete platform evidence before introducing a more flexible generative model. It makes behavior easier to test and reason about.

## “Is it production ready?”

> No. It is an engineering/portfolio prototype with production-inspired patterns: persistence, orchestration, governance, monitoring, tests, CI and containerized services.

---

# 53. Current architectural caveat worth knowing

The Streamlit application is being migrated incrementally toward a cleaner API-client boundary.

Newer operational pages such as Freshness, Volume and Observability use dedicated API service clients.

Some older analytical pages still call core modules or repositories directly.

This is known technical debt, not something to hide.

A good explanation is:

> I first stabilized the business capabilities, then started extracting UI-to-API service boundaries incrementally so I could refactor without breaking the existing demo flow.

---

# 54. End-of-demo summary

A strong final sentence is:

> **AI Data Trust Platform demonstrates how raw data can move through provenance, contracts, quality validation, governance, lifecycle control, orchestration and observability before being treated as trusted data, while a grounded AI layer explains the resulting evidence.**

That sentence represents the project better than listing every library independently.

---

# 55. Next evolution after the current showcase checkpoint

The next additions should be treated as architecture-driven upgrades rather than random technology collection.

Potential directions include:

```text
Object storage / data lake
    ↓
warehouse / analytical serving layer
    ↓
Spark for distributed processing where justified
    ↓
Kafka / event-driven ingestion where justified
    ↓
stronger API/UI boundary
    ↓
richer AI explanation layer
    ↓
final UI/UX polish
    ↓
deployment / cloud packaging
```

The rule should be:

> Add a technology when it solves a clear platform problem, not simply because it is popular.

This keeps the project coherent as it grows.
