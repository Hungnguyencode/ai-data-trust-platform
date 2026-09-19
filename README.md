# AI-assisted Data Trust Platform

[![CI](https://github.com/Hungnguyencode/ai-data-trust-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Hungnguyencode/ai-data-trust-platform/actions/workflows/ci.yml)

A portfolio-grade data platform prototype for evaluating whether a dataset is trustworthy enough to be used for analytics, dashboards, or AI/ML workloads.

The platform combines **Data Engineering, Data Quality, Governance, Observability, Orchestration, and an evidence-grounded AI Assistant** in one end-to-end system.

---

## Why this project exists

A dataset arriving in a system does not automatically mean that it is trustworthy.

Before data is promoted for downstream use, a data platform may need to answer questions such as:

- Where did this dataset come from?
- Is this a new version or an already known dataset?
- Does it still satisfy its Data Contract?
- Are important quality rules violated?
- Is sensitive information present?
- Has the data distribution drifted?
- Is the dataset fresh enough?
- Did its row volume suddenly drop or spike?
- Has governance approved the dataset?
- Which version is currently ACTIVE?
- What happened during previous pipeline runs?
- Can the platform explain the evidence behind its decisions?

**AI-assisted Data Trust Platform** models this workflow as a governed and observable data platform rather than a standalone data-analysis script.

---

## Platform capabilities

| Area | Capabilities |
|---|---|
| Ingestion | CSV, Excel and JSON ingestion, Raw/Bronze persistence, SHA-256 provenance |
| Catalog | Dataset catalog, ingestion history and content-based versioning |
| Data Contracts | Versioned contracts, schema/type validation, BLOCK/WARN enforcement |
| Profiling | Schema inference, missing values, duplicates and statistical summaries |
| Data Quality | Rule-based validation, severity classification and quality issues |
| Trust Scoring | Weighted Data Trust Score, risk level and AI-readiness assessment |
| Advanced Checks | Anomaly detection, drift detection and privacy risk scanning |
| Governance | Validation Gate, governance decision and controlled promotion |
| Lifecycle | NEW, VALIDATED, QUARANTINED, ACTIVE and SUPERSEDED states |
| Lineage | End-to-end dataset-version timeline and governance evidence |
| Persistence | SQL Server repositories for scans, datasets, runs and monitoring history |
| API | FastAPI endpoints for platform workflows and operational data |
| UI | Multi-page Streamlit application and observability dashboards |
| Orchestration | Apache Airflow DAGs for pipeline execution and scheduled monitors |
| Observability | Pipeline runs, operational events, Freshness and Volume monitoring |
| Monitoring | Prometheus metrics and Grafana dashboards |
| AI | Evidence-grounded assistant with deterministic reasoning and optional LLM enhancement |
| Engineering | Docker Compose, GitHub Actions, Ruff, pytest and health/readiness probes |

---

## Architecture

```mermaid
flowchart TB
    USER[User / Data Engineer]

    USER --> UI[Streamlit UI]
    USER --> API[FastAPI]

    UI --> API
    UI --> CORE

    AIRFLOW[Apache Airflow] --> CORE

    subgraph CORE[Data Trust Core]
        INGEST[Ingestion & Provenance]
        PROFILE[Profiling]
        CONTRACT[Data Contracts]
        QUALITY[Quality Validation]
        SCORE[Trust Scoring]
        ADVANCED[Anomaly / Drift / Privacy]
        GOVERNANCE[Governance]
        LIFECYCLE[Lifecycle & Promotion]
        LINEAGE[Lineage]
        OBS[Freshness / Volume Monitoring]
    end

    INGEST --> PROFILE
    PROFILE --> CONTRACT
    CONTRACT --> QUALITY
    QUALITY --> SCORE
    SCORE --> ADVANCED
    ADVANCED --> GOVERNANCE
    GOVERNANCE --> LIFECYCLE
    LIFECYCLE --> LINEAGE

    CORE --> SQL[(SQL Server)]
    CORE --> STORAGE[(Raw / Processed / Quarantine Artifacts)]

    API --> AI[Evidence-grounded AI Assistant]

    API --> METRICS[/Prometheus Metrics/]
    METRICS --> PROM[Prometheus]
    PROM --> GRAFANA[Grafana]

    OBS --> EVENTS[Operational Events]
    EVENTS --> SQL
```

The project deliberately keeps core data-trust logic outside the presentation layer so that the same business rules can be reused by Streamlit, FastAPI, Airflow and tests.

---

## Governed dataset workflow

```mermaid
flowchart LR
    A[Upload Dataset]
    --> B[Raw / Bronze Ingestion]
    --> C[SHA-256 Provenance]
    --> D[Catalog & Version Registration]
    --> E[Data Contract Gate]
    --> F[Profiling & Quality Validation]
    --> G[Trust / Privacy Evidence]
    --> H[Governance Decision]
    --> I[Lifecycle Synchronization]

    I -->|Eligible| J[Manual Promotion]
    J --> K[ACTIVE]

    I -->|Rejected| L[QUARANTINED]

    K --> M[New approved version]
    M --> N[Previous ACTIVE becomes SUPERSEDED]
```

A key design principle is the separation between:

```text
data arrived
```

and:

```text
data is trusted, governed and approved for use
```

Ingestion therefore never makes a dataset ACTIVE automatically.

---

## Data observability

The platform includes operational monitoring on top of the governed dataset workflow.

### Dataset Freshness

Freshness policies define the maximum allowed time since the latest ingestion.

Airflow periodically evaluates enabled policies and persists checks into SQL Server.

Typical statuses:

```text
FRESH
STALE
NO_DATA
```

A STALE condition can emit an operational event without creating duplicate alerts for the same incident.

### Dataset Volume

Volume policies compare the latest ingestion row count with the previous ingestion.

The platform detects:

```text
NORMAL
DROP
SPIKE
NO_BASELINE
```

Volume checks are idempotent and threshold breaches can emit operational events.

### Observability Overview

The platform exposes a consolidated observability view containing:

- monitored datasets,
- Freshness status,
- Volume status,
- latest pipeline status,
- recent operational events,
- historical failed pipeline runs.

This is exposed through FastAPI and rendered by a dedicated Streamlit dashboard.

---

## Airflow orchestration

Apache Airflow is used for orchestration and scheduled monitoring.

Current DAG responsibilities include:

```text
ai_data_trust_pipeline
    Governed data pipeline execution

data_freshness_monitor
    Periodic Freshness policy evaluation

data_volume_monitor
    Periodic dataset row-volume evaluation
```

Freshness and Volume monitors are designed to be safe to execute repeatedly without creating duplicate monitoring records or duplicate alerts for the same event.

---

## AI Assistant

The platform now has an **evidence-grounded assistant pipeline** built on deterministic platform state.

The AI layer is deliberately separated into two responsibilities:

1. **Deterministic platform reasoning** decides the actual platform state.
2. **Optional LLM enhancement** improves how that grounded result is explained to a human.

The current catalog-level reasoning flow is:

```text
SQL Server / Platform Evidence
        ->
Platform Context
        ->
Deterministic Platform Reasoning
        ->
Structured Diagnosis
        ->
Grounded Explanation
        ->
Optional LLM Enhancement
```

Platform Context can include evidence from:

- dataset version and lifecycle,
- lineage,
- Data Contracts,
- validation results,
- governance decisions,
- Freshness monitoring,
- Volume monitoring,
- pipeline runs,
- operational events.

The deterministic reasoning layer remains the source of truth for:

- overall state such as `HEALTHY`, `ATTENTION`, or `ACTION_REQUIRED`,
- finding codes,
- severity,
- recommended-action codes,
- action priority.

The LLM is **not allowed to override these conclusions**.

Its role is limited to improving natural-language explanation while preserving the deterministic evidence and traceability produced by the platform.

The provider layer is pluggable:

```text
Grounded Explanation
        ->
LLM Provider
        |-- disabled
        |-- gemini
        |-- ollama  (future)
        `-- openai  (optional future)
```

`disabled` is the safe default, so the platform remains fully usable without an external AI provider.

When Gemini is enabled, the enhanced explanation is generated from the already-grounded deterministic result rather than directly from raw database state.

If the LLM is unavailable, the platform can fall back to the deterministic explanation instead of losing the underlying diagnosis.

The existing `/api/assistant/ask` endpoint remains available for the earlier scan-context assistant, while the catalog-level assistant endpoints expose the newer platform reasoning pipeline.

Future work can extend this grounded foundation into a conversational Copilot and controlled tool-using assistant without moving governance decisions into the LLM.

---

## FastAPI

The backend exposes health, platform, governance and observability APIs.

Selected endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness |
| `GET /ready` | Dependency readiness |
| `GET /metrics` | Prometheus metrics |
| `GET /api/info` | Platform information |
| `POST /api/workflows/run` | Governed dataset workflow |
| `GET /api/datasets/{version_id}/lineage` | Dataset lineage |
| `POST /api/datasets/{version_id}/promote` | Governed promotion |
| `POST /api/assistant/ask` | Earlier scan-context assistant |
| `GET /api/assistant/catalog/{catalog_id}/context` | Grounded platform evidence context |
| `GET /api/assistant/catalog/{catalog_id}/diagnosis` | Deterministic platform diagnosis |
| `GET /api/assistant/catalog/{catalog_id}/explanation` | Deterministic grounded explanation |
| `GET /api/assistant/catalog/{catalog_id}/enhanced-explanation` | Optional LLM-enhanced grounded explanation |
| `GET /api/scans/history` | Persisted scan history |
| `GET /api/pipeline-runs` | Pipeline run history |
| `GET /api/operational-events` | Operational event history |
| `GET /api/freshness/catalog/{catalog_id}/history` | Freshness history |
| `POST /api/freshness/catalog/{catalog_id}/check` | Run Freshness check |
| `GET /api/volume/catalog/{catalog_id}/history` | Volume history |
| `POST /api/volume/catalog/{catalog_id}/check` | Run Volume check |
| `GET /api/observability/overview` | Consolidated observability state |

Interactive OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

---

## Streamlit dashboards

The Streamlit application provides interfaces for the major platform capabilities, including:

- dataset upload and governed workflow execution,
- data profiling,
- quality issues,
- Data Trust Score,
- anomaly detection,
- drift detection,
- privacy risk,
- AI Assistant,
- dataset governance and lifecycle,
- Freshness monitoring,
- Volume monitoring,
- Data Observability Overview.

The newer observability pages use dedicated API client modules instead of embedding HTTP request logic directly inside UI code.

---

## Persistence and lineage

SQL Server stores operational and governance history including:

```text
datasets
dataset versions
ingestion events
validation results
governance decisions
lifecycle events
scan history
quality issues
pipeline runs
operational events
Freshness policies and checks
Volume policies and checks
Data Contracts
```

Dataset lineage links these records into a version-specific history so that the platform can explain how a dataset reached its current state.

---

## Monitoring

FastAPI exports Prometheus metrics through:

```text
/metrics
```

The monitoring stack contains:

```text
FastAPI
   ↓
Prometheus
   ↓
Grafana
```

Request metrics use route templates rather than raw resource IDs to avoid unnecessary Prometheus label cardinality.

Health and readiness probes are excluded from business request metrics so infrastructure polling does not distort application traffic.

---

## Technology stack

| Layer | Technologies |
|---|---|
| Language | Python 3.12 |
| Data | pandas, NumPy |
| Statistical / ML checks | SciPy / scikit-learn based detection |
| Backend | FastAPI, Pydantic |
| UI | Streamlit, Plotly |
| Database | Microsoft SQL Server, SQLAlchemy |
| Orchestration | Apache Airflow 3 |
| Monitoring | Prometheus, Grafana |
| Containers | Docker, Docker Compose |
| Testing | pytest |
| Linting | Ruff |
| CI | GitHub Actions |

---

## Repository structure

```text
ai-data-trust-platform/
├── api/                     # FastAPI routes and schemas
├── app/
│   ├── pages/               # Streamlit pages
│   └── services/            # Streamlit API clients
├── database/
│   ├── migrations/          # SQL Server migrations
│   └── repositories/        # Persistence layer
├── orchestration/
│   └── airflow/
│       └── dags/            # Airflow DAGs
├── monitoring/              # Prometheus / Grafana configuration
├── src/
│   ├── anomaly/
│   ├── assistant/
│   ├── data_contracts/
│   ├── drift/
│   ├── governance/
│   ├── ingestion/
│   ├── lifecycle/
│   ├── lineage/
│   ├── observability/
│   ├── privacy/
│   ├── profiling/
│   ├── scoring/
│   ├── validation/
│   └── workflows/
├── tests/
├── docs/
├── compose.yaml
├── Dockerfile
├── Dockerfile.airflow
└── README.md
```

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/Hungnguyencode/ai-data-trust-platform.git
cd ai-data-trust-platform
```

### 2. Create environment configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

and configure the required local values.

The LLM integration is optional. The default configuration keeps external LLM usage disabled:

```env
LLM_PROVIDER=disabled
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
LLM_TIMEOUT_SECONDS=30
```

Supported provider values currently include:

- `disabled` - safe deterministic mode with no external LLM call,
- `gemini` - Google Gemini provider.

To enable Gemini locally:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-local-api-key>
GEMINI_MODEL=gemini-3.6-flash
LLM_TIMEOUT_SECONDS=30
```

Create the Gemini API key from your Google AI project / Google AI Studio account, then store it only in your local `.env` or another secure environment-variable source.

Never paste real API keys into source files, tests, documentation, commits, or pull requests.

The provider behavior is intentionally defensive:

- `disabled` returns the deterministic grounded explanation,
- a missing Gemini API key falls back to the deterministic explanation,
- provider runtime failures fall back safely without exposing provider secrets,
- malformed LLM environment configuration is treated as server configuration error,
- CI tests mock the provider and do not require a real API key, network request, or paid LLM call.

Do not commit `.env`.

### 3. Start the core platform

```bash
docker compose up -d --build
```

### 4. Start Airflow

```bash
docker compose --profile orchestration up -d --build airflow
```

### 5. Check containers

```bash
docker compose ps
```

---

## Local services

| Service | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| FastAPI | `http://localhost:8000` |
| Swagger / OpenAPI | `http://localhost:8000/docs` |
| Airflow | `http://localhost:8080` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

---

## Development validation

Run linting:

```bash
ruff check .
```

Run the test suite:

```bash
python -m pytest -q
```

Compile project modules:

```bash
python -m compileall api src database app orchestration
```

Check whitespace problems before committing:

```bash
git diff --check
```

The project currently contains an extensive automated test suite covering core logic, repositories, APIs, monitoring behavior, Airflow integration and Streamlit API clients.

---

## Engineering decisions worth discussing

### Core logic is not owned by the UI

Business rules live in reusable modules and repositories instead of being implemented independently in each interface.

### Ingestion is not approval

A successfully ingested dataset does not automatically become ACTIVE.

Validation, governance and promotion remain separate decisions.

### Versioning uses provenance

SHA-256 based provenance allows the platform to distinguish new content from repeated ingestion events.

### Monitoring is idempotent

Repeated Airflow executions should not create duplicate Volume checks or duplicate alerts for the same incident.

### Observability uses persisted evidence

Freshness, Volume, pipeline runs and operational events are stored rather than existing only as transient dashboard state.

### Metrics are designed for bounded cardinality

FastAPI metrics use route templates instead of raw IDs.

### AI is grounded in platform evidence

The assistant is deliberately constrained to supplied context instead of presenting unsupported generated conclusions as facts.

---

## Project scope

This repository is a **portfolio and learning-oriented platform prototype**, not a production SaaS product.

It intentionally focuses on architecture, data-platform behavior, traceability and engineering practices rather than enterprise-scale infrastructure.

---

## Next development phase

The next major technical phase is a **grounded Data Trust Copilot** built on top of the current deterministic reasoning and LLM provider layers.

The platform already provides catalog-level evidence collection, deterministic diagnosis, grounded explanation, and optional LLM enhancement.

The next step is to make that foundation conversational and tool-aware without transferring governance authority to the LLM.

The target direction is:

```text
Platform Evidence
        ->
Deterministic Reasoning
        ->
Grounded Explanation
        ->
LLM Provider
        ->
Conversational Copilot
        ->
Controlled Tool Use
```

The Copilot should be able to help users investigate questions such as:

```text
Why is this dataset currently unhealthy?

What evidence caused the current diagnosis?

Which issue should be investigated first?

What changed across dataset versions?

Which platform evidence supports the recommended action?
```

Later phases may introduce controlled tool execution, where the assistant can retrieve approved platform evidence or trigger explicitly permitted operations.

The deterministic platform remains the source of truth. The LLM must not independently change governance decisions, validation outcomes, lifecycle state, finding severity, or action priority.

---

## Portfolio summary

**AI-assisted Data Trust Platform** demonstrates how data engineering, quality controls, governance, observability and AI-assisted explanation can be combined into one traceable dataset lifecycle.

It is designed to show practical understanding of:

```text
Data Engineering
Data Quality
Data Governance
Data Observability
Backend APIs
Workflow Orchestration
SQL Persistence
Testing
Containerization
Monitoring
Evidence-grounded AI
```