# V1 Product & System Acceptance

## Purpose

Define the acceptance baseline for AI Data Trust Platform v1.

This document records:

- product journey readiness
- system boundary quality
- production gaps
- prioritized follow-up work

## Status Legend

- PASS
- PARTIAL
- FAIL
- NOT_ASSESSED

## Severity

- BLOCKER
- HIGH
- MEDIUM
- LOW

## Operating Constraints

The v1 platform should remain usable as a zero-cost, self-hostable system.

Production-readiness improvements must not require paid cloud infrastructure,
commercial monitoring platforms, paid AI providers, or managed services.

Paid services may be supported as optional deployment choices, but the core
platform must retain a functional local/open-source path.

The target is:

- portfolio-complete
- production-capable
- self-hostable
- maintainable long term
- free to develop and demonstrate

Infrastructure complexity should be introduced only when it solves a demonstrated
product or operational need.

## Acceptance Matrix

| Area | Status | Severity | Notes |
| --- | --- | --- | --- |
| Core governed workflow | PASS | - | Governed path is structurally complete |
| Governance & lifecycle | PASS | - | Promotion remains explicit and policy-gated |
| Observability | PARTIAL | MEDIUM | Metrics, dashboards, request correlation, and persisted events exist; active alerting and operational objectives are not yet defined |
| AI trust controls | PASS | - | AI architecture v1 completed through #61 |
| API/application boundary | PARTIAL | HIGH | UI boundary is inconsistent |
| Database evolution | PARTIAL | HIGH | Ordered migrations exist, but applied migration history is not tracked |
| Security & configuration | PARTIAL | HIGH | Production authentication, authorization, CORS, and database privilege hardening are not yet complete |
| Reliability & recovery | PARTIAL | HIGH | Runtime failure handling is strong, but hard-crash reconciliation and database recovery procedures are incomplete |
| Testing & CI | PARTIAL | MEDIUM | CI runs linting, tests, dependency checks, compilation, and AI evaluation; coverage, migration verification, and security scanning are not yet enforced |
| Deployment | PARTIAL | HIGH | Local Docker Compose deployment is reproducible, but production artifact publishing and environment deployment are not defined |
| UI architecture | PARTIAL | HIGH | Some pages bypass API/service boundaries |
| Release readiness | PARTIAL | HIGH | CI exists, but release versioning, immutable artifacts, promotion, rollback, and post-deploy verification are not yet defined |

## Audit Findings

### A-001 - Streamlit directly accesses persistence/core layers

**Severity:** HIGH

Some Streamlit pages import database repositories and workflow/core services directly.

Target architecture:

UI -> application/API client -> FastAPI/application layer -> core/repository

Not:

UI -> repository/core directly

### A-002 - API clients are inconsistent across UI pages

**Severity:** MEDIUM

Some features use `app.services`, while Pipeline Operations and Data Contract pages contain direct HTTP request logic.

Target architecture:

All UI-facing remote access should be centralized behind application service clients.

### A-003 - Core governed workflow is structurally complete

**Severity:** LOW

The core product journey is implemented end to end:

Ingestion -> Catalog/version -> Data Contract -> Validation -> Governance -> Lifecycle

ACTIVE promotion is intentionally excluded from the automatic workflow and remains an explicit governed action.

### A-004 - Promotion policy is enforced outside the UI

**Severity:** LOW

Promotion eligibility is enforced by domain/repository logic rather than by UI controls alone.

A version must be:

- VALIDATED
- governance APPROVED
- promotion_eligible = true

before it can become ACTIVE.

### A-005 - Product journey is not yet exposed through one consistent application boundary

**Severity:** HIGH

The core workflow is complete, but some Streamlit journeys still call repositories/core services directly.

The product should expose the governed journey through stable application/API contracts before the major UI redesign.

### A-006 - Database migrations do not record applied schema history

**Severity:** HIGH

SQL migrations are ordered and written defensively, but the database does not currently record which migrations have been applied.

The current initializer discovers all SQL migration files, sorts them by filename, and executes them on every schema initialization.

For long-term schema evolution, the platform should maintain an explicit migration ledger containing at least:

- migration identifier
- migration filename
- checksum
- applied timestamp

This allows the platform to distinguish pending migrations from already applied migrations and detect modified historical migrations.

### A-007 - Database backup and restore procedure is not defined in the tracked repository

**Severity:** HIGH

No tracked backup/restore implementation or documented recovery procedure was found during the v1 audit.

A long-lived product should define and verify:

- database backup procedure
- restore procedure
- recovery verification
- ownership and expected recovery workflow

This does not require production-grade disaster recovery for v1, but the recovery path must be explicit and testable.

### A-008 - Production authentication and authorization are not implemented

**Severity:** HIGH

The current platform does not implement production user authentication or role-based authorization.

This was previously an explicit portfolio-scope limitation, but it becomes a product-readiness requirement for a long-lived deployment.

The future security boundary should support authenticated identities and authorization for privileged actions such as:

- governance decisions
- lifecycle promotion
- policy changes
- data contract changes
- administrative operations

### A-009 - API CORS policy is permissive

**Severity:** HIGH

The FastAPI application currently allows all origins, methods, and headers.

This is convenient for local development but should not be the production configuration.

CORS policy should be environment-driven and restricted to explicitly trusted frontend origins.

### A-010 - Runtime services use a privileged SQL Server account in the current Compose environment

**Severity:** HIGH

The current Compose configuration connects platform services to SQL Server using the `sa` account.

This is acceptable for a local development environment, but production-facing services should use dedicated least-privilege database identities.

Database bootstrap/migration privileges should be separated from normal application runtime privileges.

### A-011 - Environment-specific configuration is not yet explicit

**Severity:** MEDIUM

Configuration is primarily driven by individual environment variables, but the platform does not yet expose a clear development/test/production configuration policy.

Long-term operation should make environment-specific defaults and security-sensitive production requirements explicit.

### A-012 - Persisted pipeline runs are not reconciled after hard process failure

**Severity:** HIGH

Normal workflow exceptions are persisted as FAILED and surfaced through operational events.

However, the platform does not currently define a reconciliation mechanism for pipeline runs that remain RUNNING after an abrupt worker, container, or host failure.

A long-lived orchestration system should be able to identify and reconcile stale persisted runs after restart.

A future recovery mechanism should define:

- how a stale RUNNING run is detected
- how Airflow state is compared with persisted platform state
- when a run becomes FAILED or ABANDONED
- whether automatic retry is allowed
- how recovery is recorded in operational evidence

Recovery must remain idempotent so repeated reconciliation does not duplicate state transitions or alerts.

### A-013 - Monitoring does not yet provide active operational alert delivery

**Severity:** MEDIUM

The platform exposes Prometheus metrics, Grafana dashboards, structured request logs, and persisted operational events.

However, no tracked alert rules or alert-routing configuration were found during the v1 audit.

A production-facing monitoring baseline should define actionable alerts for conditions such as:

- sustained API error rate
- excessive request latency
- API or database readiness failure
- repeated pipeline failures
- critical operational events

Alerting should remain low-noise and should avoid duplicating dataset-level operational events unnecessarily.

### A-014 - Service objectives and incident response procedures are not yet defined

**Severity:** MEDIUM

The platform currently provides useful operational signals but does not define tracked SLO/SLI targets, error budgets, or incident runbooks.

A long-lived product should define a small set of measurable operating expectations and documented response procedures.

Initial objectives can remain simple, for example:

- API availability
- request error rate
- request latency
- pipeline execution success
- monitoring freshness

The platform does not need a complex SRE program for v1, but operators should know what healthy means and what to do when the system becomes unhealthy.

### A-015 - Logs are structured but not centrally aggregated

**Severity:** MEDIUM

API requests include request identifiers and structured log fields, but no centralized log aggregation or distributed tracing configuration was found in the tracked repository.

Centralized collection should be considered after the operational alerting baseline is established.

The implementation should be driven by investigation needs rather than by infrastructure complexity alone.

### A-016 - CI does not enforce code coverage

**Severity:** MEDIUM

The project includes `pytest-cov`, but the tracked CI configuration does not currently generate or enforce a coverage threshold.

A coverage percentage should not replace behavioral testing, but a modest enforced baseline can detect accidental loss of exercised code over time.

Coverage policy should prioritize critical areas such as:

- governance and lifecycle rules
- persistence and migrations
- API boundaries
- recovery behavior
- security-sensitive authorization logic

The target should be introduced gradually rather than optimized for a headline percentage.

### A-017 - Database migration and bootstrap behavior lacks dedicated automated verification

**Severity:** MEDIUM

The test suite does not currently reference the database migration/bootstrap entrypoints audited for v1.

Long-term schema evolution should include automated verification for behavior such as:

- deterministic migration ordering
- migration ledger behavior
- checksum mismatch detection
- repeated initialization
- failed migration rollback
- bootstrap against an existing database

These tests should be added alongside the future migration-ledger hardening work.

### A-018 - CI does not currently include security or dependency vulnerability scanning

**Severity:** MEDIUM

No tracked static security analysis or dependency vulnerability scan was found during the v1 audit.

The CI baseline should eventually add lightweight automated checks for:

- vulnerable Python dependencies
- obvious insecure coding patterns
- container dependency risk where practical

Security tooling should complement code review and tests rather than becoming a substitute for them.

### A-019 - Deployment currently builds from source instead of consuming immutable release artifacts

**Severity:** HIGH

The local platform can be started reproducibly with Docker Compose, but no tracked container image publishing workflow or immutable release-image strategy was found during the v1 audit.

A release process should produce versioned artifacts once and deploy the same artifact across environments.

Container images should be traceable to an exact source revision using immutable identifiers such as a Git commit SHA and, where appropriate, a release version.

Production deployment should not depend on rebuilding source independently at each destination.

### A-020 - Production environment promotion and rollback are not defined

**Severity:** HIGH

No tracked staging/production deployment workflow or deployment rollback procedure was found during the v1 audit.

A long-lived product should define:

- how a tested artifact is promoted between environments
- which configuration differs by environment
- how deployment health is verified
- what constitutes a failed deployment
- how the previous known-good version is restored

The initial implementation can remain operationally simple and does not require Kubernetes or a multi-service cloud architecture.

### A-021 - Release lifecycle is not yet formalized

**Severity:** MEDIUM

The repository has a strong CI baseline but does not currently define a formal product release lifecycle.

Release engineering should eventually define:

- versioning conventions
- release tags
- release notes or changelog
- immutable build artifacts
- release acceptance checks
- post-deployment smoke verification

Release automation should be introduced only after the deployment target and environment model are explicit.

## Gap Classification and Prioritized Roadmap

### Acceptance Decision

No BLOCKER was identified during the v1 product and system acceptance audit.

The platform has a structurally complete governed workflow and a strong
deterministic AI trust architecture.

The remaining gaps are primarily related to:

- application boundaries
- production security
- database evolution and recovery
- orchestration recovery
- operational maturity
- release engineering

The platform does not require a rewrite.

HIGH findings should be treated as architectural or operational hardening work.
MEDIUM findings should improve release confidence and long-term maintainability.
LOW findings record accepted strengths or non-blocking improvements.

A-003 and A-004 are accepted strengths and do not require corrective work.

### Graduation Targets

The project supports two valid graduation targets.

#### Portfolio-Complete

The platform is considered portfolio-complete when it:

- exposes its core journeys through consistent application boundaries
- has a coherent and polished user experience
- preserves deterministic governance and AI trust controls
- has an explicit security and configuration model
- has safe schema evolution and a documented recovery path
- handles workflow failures predictably
- remains reproducible and self-hostable
- has strong automated verification and documentation

A paid cloud deployment is not required for portfolio completion.

#### Product-Ready Baseline

The platform reaches a product-ready baseline when it additionally provides:

- immutable release artifacts
- explicit environment promotion
- deployment health verification
- rollback procedures
- active operational alerting
- measurable service objectives
- repeatable release acceptance

This baseline must remain achievable with free or self-hosted tooling.

Paid cloud infrastructure, commercial monitoring, managed services, and paid AI
providers are optional integrations rather than core platform requirements.

### Deduplicated Gap Groups

| Gap Group | Severity | Findings | Priority |
| --- | --- | --- | --- |
| Application boundary integrity | HIGH | A-001, A-002, A-005 | MUST |
| Security and configuration baseline | HIGH | A-008, A-009, A-010, A-011 | MUST |
| Database evolution and recovery | HIGH | A-006, A-007, A-017 | MUST |
| Workflow crash recovery | HIGH | A-012 | MUST |
| Operational observability maturity | MEDIUM | A-013, A-014, A-015 | SHOULD |
| CI and security assurance | MEDIUM | A-016, A-018 | SHOULD |
| Deployment and release engineering | HIGH | A-019, A-020, A-021 | PRODUCT-READY |
| Accepted governed workflow | LOW | A-003, A-004 | COMPLETE |

### Ordering Principles

Major UI redesign should begin only after the application boundary is stable.

Security, database evolution, and recovery work should establish long-term system
constraints before presentation-layer work begins depending on unstable behavior.

UI work should then improve information architecture and product journeys without
moving domain logic into Streamlit.

Operational and release engineering should harden the completed product rather
than forcing premature infrastructure complexity.

No roadmap item should introduce paid infrastructure or additional distributed
systems unless a demonstrated product requirement justifies the cost and
complexity.

### Prioritized Roadmap

#### #63 - Application Boundary Hardening

Addresses:

- A-001
- A-002
- A-005

Goal:

Establish one consistent presentation boundary before redesigning the UI.

Target architecture:

UI -> application/API client -> FastAPI/application layer -> core/repository

Streamlit pages should no longer call repositories or core workflow services
directly.

Existing behavior should be preserved while access paths are centralized.

#### #64 - Security & Configuration Baseline

Addresses:

- A-008
- A-009
- A-010
- A-011

Goal:

Introduce a deterministic security boundary without requiring a commercial
identity provider.

Scope should include:

- authenticated identity boundary
- deterministic authorization policy
- role protection for privileged actions
- environment-driven CORS
- least-privilege runtime database access
- explicit development/test/production configuration rules

LLM or Copilot behavior must never grant, infer, or override authorization.

#### #65 - Database Evolution & Recovery

Addresses:

- A-006
- A-007
- A-017

Goal:

Make schema evolution and data recovery explicit and testable.

Scope should include:

- applied migration ledger
- migration checksums
- deterministic pending-migration execution
- historical migration modification detection
- migration/bootstrap automated tests
- documented backup procedure
- documented restore procedure
- recovery verification

The implementation should remain simple enough for local and self-hosted use.

#### #66 - Reliability & Orchestration Recovery

Addresses:

- A-012

Goal:

Ensure persisted workflow state remains trustworthy after abrupt process,
container, or host failure.

Scope should include:

- stale RUNNING detection
- deterministic reconciliation
- safe terminal state transitions
- idempotent recovery
- persisted recovery evidence
- tests for interrupted workflow scenarios

A distributed heartbeat system should not be introduced unless simpler
reconciliation is insufficient.

#### #67 - Information Architecture & Design System

Goal:

Define the visual and interaction foundation for the product before large page
rewrites.

Scope should include:

- navigation hierarchy
- core user journeys
- page responsibilities
- shared layout primitives
- reusable UI components
- typography and spacing
- status and severity presentation
- empty/loading/error states

Business logic must remain outside the UI layer.

#### #68 - UI Shell & Core Journey Redesign

Goal:

Turn the current engineering interface into a coherent product shell.

The redesign should expose the governed workflow through the hardened
application boundary rather than through direct repository access.

Primary journeys should become easy to understand without requiring knowledge
of the repository architecture.

#### #69 - Dataset Trust Workspace

Goal:

Create a cohesive workspace around the platform's central product value.

The workspace should make it easy to inspect:

- dataset identity and versions
- provenance
- Data Contracts
- validation
- governance
- lifecycle state
- promotion eligibility
- Freshness and Volume evidence
- pipeline and operational history

The UI should explain why a dataset is trusted or blocked rather than merely
displaying raw records.

#### #70 - Copilot UX v2

Goal:

Improve the user experience around the completed AI trust architecture without
weakening deterministic controls.

The existing deterministic evidence planning, sufficiency, answerability,
claim isolation, and provenance architecture should remain authoritative.

Work should focus primarily on:

- discoverability
- evidence presentation
- claim-level explanations
- limitation states
- investigation workflow
- response readability

New AI capability should only be added when justified by real product feedback.

#### #71 - Observability & CI Hardening

Addresses:

- A-013
- A-014
- A-015
- A-016
- A-018

Goal:

Move from passive observability to an operationally useful free/self-hosted
baseline.

Scope should include:

- actionable Prometheus alert rules
- small SLI/SLO baseline
- incident runbooks
- code coverage reporting and a gradual enforcement policy
- dependency vulnerability scanning
- lightweight static security scanning

Centralized logging or distributed tracing should remain optional until
investigation needs demonstrate clear value.

#### #72 - Release Engineering & Graduation

Addresses:

- A-019
- A-020
- A-021

Goal:

Make a tested revision reproducibly releasable without requiring paid cloud
infrastructure.

Target flow:

tested commit
-> immutable versioned artifact
-> controlled deployment
-> health verification
-> acceptance or rollback

Scope should include:

- versioning convention
- release tags
- immutable container image identifiers
- release notes or changelog
- deployment configuration
- environment promotion rules
- post-deployment smoke verification
- rollback procedure

Docker Compose or another simple self-hosted deployment model is acceptable for
the initial product-ready baseline.

Kubernetes, managed cloud platforms, or additional distributed infrastructure
should only be introduced when actual scale or operational requirements justify
them.

## Recommended Execution Order

The recommended order is:

#63 Application Boundary Hardening
-> #64 Security & Configuration Baseline
-> #65 Database Evolution & Recovery
-> #66 Reliability & Orchestration Recovery
-> #67 Information Architecture & Design System
-> #68 UI Shell & Core Journey Redesign
-> #69 Dataset Trust Workspace
-> #70 Copilot UX v2
-> #71 Observability & CI Hardening
-> #72 Release Engineering & Graduation

This order intentionally hardens system boundaries before major visual redesign,
then improves the product experience, and finally establishes the operational
and release discipline required for long-term use.
