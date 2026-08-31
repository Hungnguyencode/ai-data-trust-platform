from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import pandas as pd


@dataclass(frozen=True)
class IngestionMetadata:
    ingestion_id: str
    source_type: str
    file_name: str
    file_type: str
    extension: str
    content_sha256: str
    byte_size: int
    row_count: int
    column_count: int
    ingested_at: str
    raw_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IngestionResult:
    dataframe: pd.DataFrame
    metadata: IngestionMetadata
