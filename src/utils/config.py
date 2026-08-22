from __future__ import annotations

from pathlib import Path

from src.utils.helpers import get_project_root


PROJECT_ROOT = get_project_root()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
BASELINE_DATA_DIR = DATA_DIR / "baseline"
CORRUPTED_DATA_DIR = DATA_DIR / "corrupted"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"