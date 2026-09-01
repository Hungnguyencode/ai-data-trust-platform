from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_engine  # noqa: E402

MIGRATION_PATH = (
    PROJECT_ROOT
    / "database"
    / "migrations"
    / "001_dataset_catalog.sql"
)


def split_sql_batches(sql_text: str) -> list[str]:
    batches = re.split(
        r"^\s*GO\s*$",
        sql_text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    return [
        batch.strip()
        for batch in batches
        if batch.strip()
    ]


def initialize_catalog_schema() -> None:
    if not MIGRATION_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy migration: {MIGRATION_PATH}"
        )

    sql_text = MIGRATION_PATH.read_text(encoding="utf-8")
    batches = split_sql_batches(sql_text)

    engine = get_engine()

    with engine.begin() as connection:
        for batch in batches:
            connection.exec_driver_sql(batch)


def main() -> None:
    initialize_catalog_schema()

    print("Dataset catalog schema initialized successfully.")
    print("Created/verified:")
    print("  - dataset_catalog")
    print("  - dataset_versions")
    print("  - ingestion_history")


if __name__ == "__main__":
    main()