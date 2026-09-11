from __future__ import annotations

import json
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.assistant import router as assistant_router
from api.routes.datasets import router as datasets_router
from api.routes.scans import router as scans_router
from api.routes.scores import router as scores_router
from api.routes.workflows import router as workflows_router
from database.db import test_connection
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


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
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

    duration_ms = round(
        (time.perf_counter() - started_at) * 1000,
        2,
    )

    response.headers["X-Request-ID"] = request_id

    if request.url.path not in {"/health", "/ready"}:
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
            "governed dataset workflow API",
            "dataset lineage API",
            "governance-aware promotion API",
            "persisted scan history API",
        ],
        "note": "This API is a minimal backend layer. Streamlit can still run independently.",
    }


app.include_router(datasets_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(scans_router, prefix="/api/scans", tags=["scans"])
app.include_router(scores_router, prefix="/api/scores", tags=["scores"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["assistant"])
app.include_router(
    workflows_router,
    prefix="/api/workflows",
    tags=["workflows"],
)