from __future__ import annotations

import os
import urllib.parse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


def build_connection_string() -> str:
    """
    Tạo connection string cho SQL Server qua SQLAlchemy + pyodbc.

    Hỗ trợ:
    - Windows Authentication
    - SQL Server Authentication
    """
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "AIDataTrustPlatform")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower()

    username = os.getenv("DB_USERNAME", "")
    password = os.getenv("DB_PASSWORD", "")

    if trusted_connection in {"yes", "true", "1"}:
        raw_connection = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    else:
        raw_connection = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )

    encoded_connection = urllib.parse.quote_plus(raw_connection)
    return f"mssql+pyodbc:///?odbc_connect={encoded_connection}"


def get_engine() -> Engine:
    """
    Tạo SQLAlchemy engine.
    """
    connection_string = build_connection_string()

    return create_engine(
        connection_string,
        pool_pre_ping=True,
        future=True,
    )


def test_connection() -> tuple[bool, str]:
    """
    Kiểm tra kết nối SQL Server.
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS ok"))
            value = result.scalar_one()

        if value == 1:
            return True, "Kết nối SQL Server thành công."

        return False, "Không nhận được phản hồi hợp lệ từ SQL Server."

    except Exception as exc:
        return False, f"Kết nối SQL Server thất bại: {exc}"