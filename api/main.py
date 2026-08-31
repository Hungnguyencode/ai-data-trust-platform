from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.assistant import router as assistant_router
from api.routes.datasets import router as datasets_router
from api.routes.scans import router as scans_router
from api.routes.scores import router as scores_router

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
        ],
        "note": "This API is a minimal backend layer. Streamlit can still run independently.",
    }


app.include_router(datasets_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(scans_router, prefix="/api/scans", tags=["scans"])
app.include_router(scores_router, prefix="/api/scores", tags=["scores"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["assistant"])