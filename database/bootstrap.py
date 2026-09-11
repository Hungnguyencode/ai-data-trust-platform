from __future__ import annotations

import os
import time
import urllib.parse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from database.init_catalog import initialize_database_schema


def build_master_connection_string() -> str:
    """
    Build a SQL Server connection string targeting the master database.

    This is used before AIDataTrustPlatform exists so the bootstrap
    process can create the application database.
    """
    server = os.getenv("DB_SERVER", "localhost")
    driver = os.getenv(
        "DB_DRIVER",
        "ODBC Driver 17 for SQL Server",
    )
    trusted_connection = os.getenv(
        "DB_TRUSTED_CONNECTION",
        "yes",
    ).lower()

    username = os.getenv("DB_USERNAME", "")
    password = os.getenv("DB_PASSWORD", "")

    if trusted_connection in {"yes", "true", "1"}:
        raw_connection = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            "DATABASE=master;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    else:
        if not username or not password:
            raise RuntimeError(
                "DB_USERNAME and DB_PASSWORD are required "
                "when DB_TRUSTED_CONNECTION=no."
            )

        raw_connection = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            "DATABASE=master;"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )

    encoded_connection = urllib.parse.quote_plus(
        raw_connection
    )

    return (
        "mssql+pyodbc:///?odbc_connect="
        f"{encoded_connection}"
    )


def wait_for_sql_server(
    max_attempts: int = 60,
    retry_seconds: float = 2.0,
) -> Engine:
    """
    Wait until SQL Server accepts connections.

    SQL Server containers can take several seconds to become ready,
    so bootstrap must not assume the server is immediately available.
    """
    engine = create_engine(
        build_master_connection_string(),
        pool_pre_ping=True,
        future=True,
        isolation_level="AUTOCOMMIT",
    )

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(
                    text("SELECT 1")
                )

            print(
                "SQL Server is ready "
                f"(attempt {attempt}/{max_attempts})."
            )
            return engine

        except Exception as exc:
            if attempt == max_attempts:
                engine.dispose()
                raise RuntimeError(
                    "SQL Server did not become ready "
                    f"after {max_attempts} attempts."
                ) from exc

            print(
                "Waiting for SQL Server "
                f"({attempt}/{max_attempts})..."
            )
            time.sleep(retry_seconds)

    raise RuntimeError(
        "Unexpected SQL Server bootstrap state."
    )


def ensure_application_database(
    master_engine: Engine,
) -> None:
    """
    Create the application database when it does not yet exist.
    """
    database_name = os.getenv(
        "DB_NAME",
        "AIDataTrustPlatform",
    )

    with master_engine.connect() as connection:
        database_id = connection.execute(
            text("SELECT DB_ID(:database_name)"),
            {
                "database_name": database_name,
            },
        ).scalar_one_or_none()

        if database_id is not None:
            print(
                f"Database already exists: {database_name}"
            )
            return

        escaped_database_name = (
            database_name.replace("]", "]]")
        )

        print(
            f"Creating database: {database_name}"
        )

        connection.exec_driver_sql(
            f"CREATE DATABASE "
            f"[{escaped_database_name}]"
        )

        print(
            f"Database created: {database_name}"
        )


def main() -> None:
    print("Starting database bootstrap...")

    master_engine = wait_for_sql_server()

    try:
        ensure_application_database(
            master_engine
        )
    finally:
        master_engine.dispose()

    print("Running database migrations...")

    initialize_database_schema()

    print("")
    print(
        "Database bootstrap completed successfully."
    )


if __name__ == "__main__":
    main()