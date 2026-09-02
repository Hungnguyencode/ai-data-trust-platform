from __future__ import annotations

import hashlib
from io import BytesIO

import pandas as pd
import pytest

from src.ingestion.file_loader import (
    get_file_type,
    load_dataset,
    validate_file_extension,
)
from src.ingestion.ingestion_service import ingest_dataset
from src.ingestion.raw_storage import sanitize_file_name


class NamedBytesIO(BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def build_csv_file() -> NamedBytesIO:
    return NamedBytesIO(
        b"customer_id,age,city\n1,25,Hanoi\n2,30,HCM\n",
        "customers.csv",
    )


def test_supported_file_extension():
    validate_file_extension("customers.csv")
    validate_file_extension("customers.xlsx")
    validate_file_extension("customers.json")


def test_unsupported_file_extension_is_rejected():
    with pytest.raises(ValueError, match="chưa được hỗ trợ"):
        validate_file_extension("customers.txt")


def test_file_type_mapping():
    assert get_file_type("customers.csv") == "CSV"
    assert get_file_type("customers.xlsx") == "Excel"
    assert get_file_type("customers.json") == "JSON"


def test_load_dataset_keeps_backward_compatible_contract():
    uploaded_file = build_csv_file()

    df, file_type = load_dataset(uploaded_file)

    assert isinstance(df, pd.DataFrame)
    assert file_type == "CSV"
    assert df.shape == (2, 3)
    assert list(df.columns) == ["customer_id", "age", "city"]


def test_ingestion_generates_metadata_and_checksum(tmp_path):
    uploaded_file = build_csv_file()
    expected_content = uploaded_file.getvalue()

    result = ingest_dataset(
        uploaded_file,
        raw_root=tmp_path,
    )

    metadata = result.metadata

    assert result.dataframe.shape == (2, 3)

    assert metadata.file_name == "customers.csv"
    assert metadata.file_type == "CSV"
    assert metadata.extension == ".csv"
    assert metadata.source_type == "upload"

    assert metadata.byte_size == len(expected_content)
    assert metadata.row_count == 2
    assert metadata.column_count == 3

    assert metadata.content_sha256 == hashlib.sha256(
        expected_content
    ).hexdigest()

    assert metadata.ingestion_id
    assert metadata.ingested_at
    assert metadata.raw_path is not None


def test_ingestion_persists_original_raw_bytes(tmp_path):
    uploaded_file = build_csv_file()
    expected_content = uploaded_file.getvalue()

    result = ingest_dataset(
        uploaded_file,
        raw_root=tmp_path,
    )

    raw_path = result.metadata.raw_path

    assert raw_path is not None

    with open(raw_path, "rb") as file:
        stored_content = file.read()

    assert stored_content == expected_content


def test_identical_content_has_same_checksum_and_raw_location(tmp_path):
    first_file = build_csv_file()
    second_file = build_csv_file()

    first_result = ingest_dataset(
        first_file,
        raw_root=tmp_path,
    )
    second_result = ingest_dataset(
        second_file,
        raw_root=tmp_path,
    )

    assert (
        first_result.metadata.content_sha256
        == second_result.metadata.content_sha256
    )

    assert first_result.metadata.raw_path == second_result.metadata.raw_path

    assert (
        first_result.metadata.ingestion_id
        != second_result.metadata.ingestion_id
    )


def test_raw_storage_sanitizes_external_file_name():
    assert sanitize_file_name("../../customers.csv") == "customers.csv"
    assert sanitize_file_name(r"..\..\customers.csv") == "customers.csv"


def test_empty_dataset_is_rejected():
    uploaded_file = NamedBytesIO(
        b"customer_id,age\n",
        "empty.csv",
    )

    with pytest.raises(ValueError, match="Dataset rỗng"):
        ingest_dataset(
            uploaded_file,
            persist_raw=False,
        )
