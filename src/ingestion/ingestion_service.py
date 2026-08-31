from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.ingestion.contracts import IngestionMetadata, IngestionResult
from src.ingestion.file_loader import load_dataset_from_bytes, read_source_bytes
from src.ingestion.raw_storage import DEFAULT_RAW_ROOT, store_raw_artifact


def calculate_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def ingest_dataset(
    source,
    *,
    persist_raw: bool = True,
    raw_root: Path | str = DEFAULT_RAW_ROOT,
) -> IngestionResult:
    """
    Main entrypoint for dataset ingestion.

    Pipeline:
        source
        -> raw bytes
        -> checksum
        -> DataFrame parsing
        -> optional immutable raw storage
        -> ingestion metadata
    """
    content, file_name, source_type = read_source_bytes(source)

    checksum = calculate_sha256(content)

    df, file_type = load_dataset_from_bytes(
        content=content,
        file_name=file_name,
    )

    raw_path = None

    if persist_raw:
        stored_path = store_raw_artifact(
            content=content,
            file_name=file_name,
            content_sha256=checksum,
            raw_root=raw_root,
        )
        raw_path = str(stored_path)

    metadata = IngestionMetadata(
        ingestion_id=str(uuid.uuid4()),
        source_type=source_type,
        file_name=file_name,
        file_type=file_type,
        extension=Path(file_name).suffix.lower(),
        content_sha256=checksum,
        byte_size=len(content),
        row_count=int(df.shape[0]),
        column_count=int(df.shape[1]),
        ingested_at=datetime.now(timezone.utc).isoformat(),
        raw_path=raw_path,
    )

    return IngestionResult(
        dataframe=df,
        metadata=metadata,
    )
