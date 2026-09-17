# Dataset and Artifact Guide

## 1. Purpose

This document explains how datasets move through **AI-assisted Data Trust Platform**, which local data directories are used, and how to prepare a dataset for the main demo flows.

The project treats an uploaded file as more than an in-memory DataFrame. A dataset can produce:

- a Raw/Bronze artifact,
- ingestion metadata and SHA-256 provenance,
- a catalog entry and dataset version,
- Data Contract validation evidence,
- data-quality validation results,
- governance decisions,
- lifecycle transitions,
- persisted scan history,
- Freshness and Volume monitoring history,
- reports and operational events.

The most important distinction is:

```text
data arrived
```

is not the same as:

```text
data is trusted and approved for downstream use
```

---

## 2. Supported Input Formats

The ingestion layer currently supports:

| Format | Typical extension |
|---|---|
| CSV | `.csv` |
| Excel | `.xlsx`, `.xls` |
| JSON | `.json` |

Files are validated before ingestion. The ingestion layer normalizes the file name, reads the dataset, calculates a SHA-256 content hash, and records provenance metadata.

---

## 3. Data Directory Layout

The project uses the local `data/` directory for runtime artifacts and demo datasets.

```text
data/
├── baseline/
├── corrupted/
├── lifecycle_test/
├── processed/
├── quarantine/
├── raw/
└── reports/
```

Some of these directories are runtime artifact locations and are intentionally ignored by Git.

### `data/raw/`

Stores the original Raw/Bronze artifact produced during ingestion.

Typical responsibilities:

- preserve the source payload,
- provide reproducibility,
- retain the original file before downstream validation,
- support lineage through the stored `raw_path`.

Example conceptual path:

```text
data/raw/sample_customers.csv
```

The project does not treat the Raw/Bronze artifact as trusted data. It is simply the preserved source input.

### `data/processed/`

Stores datasets that pass the technical Validation Gate.

The current validation policy treats **High** severity quality issues as blocking.

Conceptually:

```text
no High issue
    -> ACCEPTED
    -> data/processed/
```

The UI describes these artifacts as validated data / Silver candidates.

A validation metadata file is stored alongside the validated artifact.

Example:

```text
data/processed/customers.csv
data/processed/customers.validation.json
```

### `data/quarantine/`

Stores datasets rejected by the technical Validation Gate.

Conceptually:

```text
one or more High issues
    -> REJECTED
    -> data/quarantine/
```

A quarantined dataset cannot be promoted to `ACTIVE`.

Example:

```text
data/quarantine/customers.csv
data/quarantine/customers.validation.json
```

### `data/baseline/`

Reserved for baseline datasets used in comparison-oriented flows such as Drift Detection.

The Drift page can compare:

```text
baseline dataset
vs
current dataset
```

The comparison can include:

- schema drift,
- PSI,
- KS-test evidence,
- categorical distribution differences.

The UI can also use the dataset currently loaded in the Streamlit session as the current dataset.

### `data/corrupted/`

Reserved for intentionally degraded or problematic data used for experiments, validation scenarios, or demonstrations.

This directory is useful when a demo needs to show how the platform behaves when data quality deteriorates.

### `data/reports/`

Stores generated HTML reports.

The Reports page can:

- generate an HTML report from the current session,
- download it,
- optionally persist it to `data/reports/`.

The current project recommends using the browser's print flow if a PDF copy is needed.

### `data/lifecycle_test/`

Used for local lifecycle and orchestration demo data.

The main Airflow governed pipeline currently uses this default container path:

```text
/app/data/lifecycle_test/v3/sample_customers.csv
```

This path is the default source for the `ai_data_trust_pipeline` DAG.

`data/lifecycle_test/` is a local runtime/demo area and is ignored by Git, so a fresh clone may require the demo fixture to be created or copied locally before that DAG is executed.

---

## 4. Primary Demo Dataset

The project currently uses `sample_customers.csv` as the main lifecycle/orchestration fixture.

The Airflow default source is:

```text
/app/data/lifecycle_test/v3/sample_customers.csv
```

The exact business content of the file is less important than the platform behavior it triggers.

The dataset is used to demonstrate the governed processing path:

```text
File
  ↓
Raw/Bronze ingestion
  ↓
SHA-256 provenance
  ↓
Catalog registration
  ↓
Version registration
  ↓
Data Contract Gate
  ↓
Profiling
  ↓
Quality Validation
  ↓
Trust Score / Privacy evidence
  ↓
Governance Decision
  ↓
Lifecycle synchronization
  ↓
Optional manual promotion
```

---

## 5. Ingestion Provenance

Each ingestion records provenance information such as:

- ingestion identifier,
- normalized file name,
- file type,
- content SHA-256,
- byte size,
- source type,
- raw artifact path.

The SHA-256 is important because dataset versioning is content-aware.

Conceptually:

```text
same logical dataset
+ same SHA-256
= reuse the known version and record another ingestion event
```

while:

```text
same logical dataset
+ different SHA-256
= create a new dataset version
```

This allows the project to preserve the history of a logical dataset instead of blindly overwriting it.

---

## 6. Catalog and Versioning

After ingestion, the dataset is registered in the SQL Server catalog.

A logical dataset may have multiple versions.

Example:

```text
Catalog 1
├── v1
├── v2
└── v3
```

Each version can have its own:

- content hash,
- row count,
- lifecycle state,
- validation evidence,
- governance evidence,
- contract-validation evidence,
- ingestion history.

This version history is later reused by Lineage, Freshness, Volume Monitoring, and promotion logic.

---

## 7. Data Contract Evidence

A catalog can have a versioned Data Contract.

The current contract model can define, per column:

- column name,
- expected logical type,
- whether the column is required,
- whether the column may be nullable.

Supported contract types include:

```text
NUMERIC
CATEGORICAL
DATETIME
BOOLEAN
TEXT
```

A contract can be enforced in:

```text
BLOCK
WARN
```

mode.

A dataset can therefore be classified as contract-compatible or breaking before the rest of the governed workflow proceeds.

---

## 8. Technical Validation

The Validation Gate answers a technical question:

> Does this dataset satisfy the current data-quality policy?

The current validation policy uses issue severity.

```text
High severity issue
    -> blocking

Medium / Low issue
    -> recorded but non-blocking
```

The resulting validation status is typically:

```text
ACCEPTED
REJECTED
```

An accepted dataset is routed to `data/processed/`.

A rejected dataset is routed to `data/quarantine/`.

---

## 9. Governance and Lifecycle

Technical validation and governance are separate concerns.

Validation asks:

> Is the dataset technically acceptable?

Governance asks:

> Based on the available evidence, should this dataset be allowed to progress?

The lifecycle currently models:

```text
NEW
VALIDATED
QUARANTINED
ACTIVE
SUPERSEDED
```

A newly ingested dataset is not automatically `ACTIVE`.

Promotion is deliberately controlled.

A typical successful progression is:

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

When a newer version becomes `ACTIVE`, an older active version can become:

```text
SUPERSEDED
```

A rejected version can become:

```text
QUARANTINED
```

and cannot be promoted.

---

## 10. Dataset Lineage

The platform can reconstruct end-to-end lineage for a dataset version.

The lineage response combines evidence such as:

- version metadata,
- ingestion events,
- Data Contract validations,
- technical validations,
- governance decisions,
- lifecycle events,
- chronological timeline.

The goal is to answer:

```text
Where did this dataset come from?
What happened to it?
Why is it in its current state?
```

---

## 11. Data Quality and Trust Evaluation

The analytical pages operate on the dataset loaded in the Streamlit session.

The current evaluation flow can include:

- profiling,
- missing-value analysis,
- duplicate detection,
- type/range/categorical validation,
- Data Trust Score,
- anomaly detection,
- privacy-risk scanning,
- drift analysis.

The Trust Score is not the lifecycle state itself.

It is one piece of evidence used by the platform.

---

## 12. Anomaly Detection Dataset Requirements

The anomaly engine primarily benefits from numeric columns.

The current UI exposes:

- IQR,
- Z-score,
- Isolation Forest.

A useful anomaly demo dataset should therefore contain:

- multiple numeric columns,
- mostly regular observations,
- a few intentionally unusual values.

If no usable numeric columns exist, some anomaly methods cannot provide meaningful evidence.

---

## 13. Drift Detection Dataset Requirements

Drift Detection compares two datasets:

```text
baseline
vs
current
```

A useful drift demo should keep some common columns while modifying selected characteristics.

Examples:

- change a numeric distribution,
- change category proportions,
- add or remove a column,
- change a column's inferred type.

The current implementation can expose:

- schema changes,
- numeric PSI,
- numeric KS-test evidence,
- categorical distribution differences.

The baseline and current datasets should represent the same logical subject when the goal is to demonstrate meaningful drift.

---

## 14. Privacy Demo Data

The current privacy scanner is rule-based.

It can look for evidence such as:

- email-like values,
- phone-like values,
- citizen-ID-like values,
- column-name heuristics associated with names,
- address-like columns.

For a privacy-risk demo, use synthetic values only.

Do not place real personal data, credentials, tokens, or private customer information in the repository.

---

## 15. Freshness Monitoring Data

Freshness monitoring is based on persisted ingestion history.

For an enabled Freshness Policy, the monitor evaluates the time since the latest ingestion against:

```text
max_age_minutes
```

Typical statuses are:

```text
FRESH
STALE
NO_DATA
```

The scheduled Airflow monitor can periodically persist these checks.

When a dataset becomes stale, the platform can emit an operational event without continuously duplicating the same alert.

---

## 16. Volume Monitoring Data

Volume Monitoring compares the row count of the newest ingestion with the previous ingestion for the same catalog.

Example:

```text
previous ingestion: 7 rows
current ingestion: 8 rows

row change = +14.2857%
```

The policy uses:

- drop threshold percentage,
- spike threshold percentage.

Typical statuses are:

```text
NORMAL
DROP
SPIKE
NO_BASELINE
```

The first comparable ingestion may not have a baseline yet.

`DROP` and `SPIKE` can emit operational alerts.

Checks and alerts are designed to remain idempotent for the same ingestion event.

---

## 17. Recommended Local Demo Scenarios

A compact portfolio demo can use several dataset states.

### Scenario A — Healthy dataset

Use a dataset with:

- expected schema,
- low missingness,
- no blocking issue,
- acceptable privacy evidence.

Goal:

```text
ACCEPTED
→ Governance APPROVED
→ VALIDATED
→ manual promotion
→ ACTIVE
```

### Scenario B — Quality failure

Introduce a blocking quality issue.

Goal:

```text
REJECTED
→ QUARANTINED
```

Use this to show that arrival does not imply trust.

### Scenario C — New version

Modify the content of the same logical dataset.

Goal:

```text
different SHA-256
→ new dataset version
```

Use this to demonstrate version history and lineage.

### Scenario D — Contract violation

Change or remove a contracted column.

Goal:

```text
Data Contract validation
→ COMPATIBLE or BREAKING
```

Use `BLOCK` and `WARN` to explain enforcement behavior.

### Scenario E — Drift

Compare a stable baseline with a deliberately changed current dataset.

Goal:

```text
schema / numeric / categorical drift evidence
```

### Scenario F — Freshness breach

Allow the latest ingestion to become older than the configured SLA.

Goal:

```text
FRESH
→ STALE
→ operational event
```

### Scenario G — Volume breach

Create a new ingestion whose row count differs enough to cross the policy threshold.

Goal:

```text
NORMAL
→ DROP or SPIKE
→ operational event
```

---

## 18. Safe Portfolio Data Guidance

Repository examples should preferably be:

- synthetic,
- anonymized,
- small enough for a local demo,
- deterministic enough for reproducible tests,
- free of credentials and real secrets.

Never commit:

- database passwords,
- API keys,
- private production datasets,
- real PII,
- authentication tokens.

Runtime secrets belong in environment configuration such as `.env`, while public examples belong in `.env.example`.

---

## 19. Reproducibility Notes

A fresh checkout may not contain every runtime artifact because several data directories are ignored by Git.

This is expected.

The source-controlled project contains the platform logic, while runtime execution can create:

```text
Raw/Bronze artifacts
validated artifacts
quarantined artifacts
reports
database history
monitoring history
```

For a portfolio demo, keep the setup steps in `run_demo.md` so another developer can reconstruct the expected local state.

---

## 20. Summary

The project treats a dataset as a versioned, governed entity rather than a temporary DataFrame.

The intended lifecycle is:

```text
Input file
   ↓
Raw/Bronze preservation
   ↓
Provenance + SHA-256
   ↓
Catalog + Version
   ↓
Contract / Quality evaluation
   ↓
Governance evidence
   ↓
Lifecycle state
   ↓
Controlled promotion
   ↓
Operational monitoring
```

This data model supports the broader project goal: demonstrating how a Data Engineering platform can make data quality, trust, governance, lineage, orchestration, and observability part of one coherent workflow.
