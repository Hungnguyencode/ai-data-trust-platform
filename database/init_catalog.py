from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_engine  # noqa: E402

MIGRATIONS_DIR = (
    PROJECT_ROOT
    / "database"
    / "migrations"
)


def split_sql_batches(
    sql_text: str,
) -> list[str]:
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


def get_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        raise FileNotFoundError(
            f"Không tìm thấy migration directory: "
            f"{MIGRATIONS_DIR}"
        )

    migration_files = sorted(
        MIGRATIONS_DIR.glob("*.sql")
    )

    if not migration_files:
        raise RuntimeError(
            "Không tìm thấy SQL migration nào."
        )

    return migration_files


def run_migration(
    migration_path: Path,
) -> None:
    sql_text = migration_path.read_text(
        encoding="utf-8"
    )

    batches = split_sql_batches(
        sql_text
    )

    engine = get_engine()

    with engine.begin() as connection:
        for batch in batches:
            connection.exec_driver_sql(
                batch
            )


def initialize_database_schema() -> None:
    migration_files = get_migration_files()

    print(
        f"Found {len(migration_files)} migration(s)."
    )

    for migration_path in migration_files:
        print(
            f"Running: {migration_path.name}"
        )

        run_migration(
            migration_path
        )

        print(
            f"OK: {migration_path.name}"
        )


def main() -> None:
    initialize_database_schema()

    print("")
    print(
        "Database migrations completed successfully."
    )


if __name__ == "__main__":
    main()