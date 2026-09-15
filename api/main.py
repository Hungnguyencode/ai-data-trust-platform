from __future__ import annotations

import json
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.routing import iter_route_contexts
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.routes.assistant import router as assistant_router
from api.routes.data_contracts import (
    router as data_contracts_router,
)
from api.routes.datasets import router as datasets_router
from api.routes.operational_events import (
    router as operational_events_router,
)
from api.routes.pipeline_runs import router as pipeline_runs_router
from api.routes.scans import router as scans_router
from api.routes.scores import router as scores_router
from api.routes.workflows import router as workflows_router
from database.db import test_connection
from src.observability.metrics import observe_http_request
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="AI Data Trust Platform API",
    description="Minimal FastAPI backend for AI-assisted Data Trust Platform.",
    version="2.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


EXCLUDED_METRIC_PATHS = {
    "/health",
    "/ready",
    "/metrics",
}


def resolve_metric_path(request: Request) -> str:
    """
    Resolve the full low-cardinality FastAPI route template.

    Examples:
    /api/scans/history
    /api/scans/{scan_id}
    /api/datasets/{version_id}/lineage
    """

    scope = dict(request.scope)

    scope["path"] = request.url.path
    scope["raw_path"] = request.url.path.encode("utf-8")
    scope["root_path"] = ""

    partial_match_path = None

    for route_context in iter_route_contexts(
        request.app.router.routes
    ):
        match, _ = route_context.matches(scope)

        route_path = (
            getattr(
                route_context,
                "path_format",
                None,
            )
            or getattr(
                route_context,
                "path",
                None,
            )
        )

        if match.name == "FULL" and route_path:
            return str(route_path)

        if (
            match.name == "PARTIAL"
            and route_path
            and partial_match_path is None
        ):
            partial_match_path = str(
                route_path
            )

    return (
        partial_match_path
        or "__unmatched__"
    )


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid4())
    )

    started_at = time.perf_counter()

    metric_path = resolve_metric_path(
        request
    )

    should_observe = (
        request.url.path
        not in EXCLUDED_METRIC_PATHS
    )

    try:
        response = await call_next(
            request
        )

    except Exception:
        duration_seconds = (
            time.perf_counter()
            - started_at
        )

        duration_ms = round(
            duration_seconds * 1000,
            2,
        )

        if should_observe:
            observe_http_request(
                method=request.method,
                path=metric_path,
                status_code=500,
                duration_seconds=duration_seconds,
            )

            logger.exception(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": 500,
                        "duration_ms": duration_ms,
                    },
                    ensure_ascii=False,
                )
            )

        raise

    duration_seconds = (
        time.perf_counter()
        - started_at
    )

    duration_ms = round(
        duration_seconds * 1000,
        2,
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    if should_observe:
        observe_http_request(
            method=request.method,
            path=metric_path,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )

        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
            )
        )

    return response


@app.get("/")
def root():
    return {
        "app": "AI Data Trust Platform API",
        "version": "2.6.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-data-trust-api",
        "version": "2.6.0",
    }


@app.get("/ready")
def readiness_check():
    database_ok, _ = test_connection()

    payload = {
        "status": "ready" if database_ok else "not_ready",
        "service": "ai-data-trust-api",
        "version": "2.6.0",
        "dependencies": {
            "sqlserver": "ok" if database_ok else "unavailable",
        },
    }

    if database_ok:
        return payload

    return JSONResponse(
        status_code=503,
        content=payload,
    )


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/api/info")
def api_info():
    return {
        "name": "AI-assisted Data Trust Platform",
        "version": "2.6.0",
        "features": [
            "dataset profiling",
            "quality checking",
            "trust scoring",
            "anomaly detection",
            "privacy risk scanning",
            "drift detection",
            "report generation",
            "rule-grounded assistant",
            "FastAPI assistant endpoint",
            "column-level cleaning plan",
            "data contract enforcement",
            "data contract management API",
            "governed dataset workflow API",
            "contract-aware dataset lineage API",
            "governance-aware promotion API",
            "persisted scan history API",
            "pipeline operations API",
            "operational alerts API",
        ],
        "note": "This API is a minimal backend layer. Streamlit can still run independently.",
    }


app.include_router(datasets_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(scans_router, prefix="/api/scans", tags=["scans"])
app.include_router(scores_router, prefix="/api/scores", tags=["scores"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["assistant"])
app.include_router(
    data_contracts_router,
    prefix="/api/data-contracts",
    tags=["data-contracts"],
)
app.include_router(
    workflows_router,
    prefix="/api/workflows",
    tags=["workflows"],
)
app.include_router(
    pipeline_runs_router,
    prefix="/api/pipeline-runs",
    tags=["pipeline-runs"],
)
app.include_router(
    operational_events_router,
    prefix="/api/operational-events",
    tags=["operational-events"],
)