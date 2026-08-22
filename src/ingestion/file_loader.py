from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


def validate_file_extension(file_name: str) -> None:
    """
    Kiểm tra định dạng file có được hỗ trợ hay không.
    """
    suffix = Path(file_name).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Định dạng file '{suffix}' chưa được hỗ trợ. "
            f"Các định dạng hợp lệ: {supported}"
        )


def load_dataset(uploaded_file) -> Tuple[pd.DataFrame, str]:
    """
    Đọc dataset từ file được upload qua Streamlit.

    Hỗ trợ:
    - CSV
    - Excel
    - JSON

    Returns:
        df: DataFrame đã đọc
        file_type: loại file
    """
    if uploaded_file is None:
        raise ValueError("Chưa có file nào được upload.")

    file_name = uploaded_file.name
    validate_file_extension(file_name)

    suffix = Path(file_name).suffix.lower()

    try:
        if suffix == ".csv":
            df = pd.read_csv(uploaded_file)
            file_type = "CSV"

        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(uploaded_file)
            file_type = "Excel"

        elif suffix == ".json":
            df = pd.read_json(uploaded_file)
            file_type = "JSON"

        else:
            raise ValueError(f"Định dạng file không hợp lệ: {suffix}")

    except Exception as exc:
        raise ValueError(f"Không thể đọc file '{file_name}'. Chi tiết lỗi: {exc}") from exc

    if df.empty:
        raise ValueError("Dataset rỗng. Vui lòng upload file có dữ liệu.")

    return df, file_type