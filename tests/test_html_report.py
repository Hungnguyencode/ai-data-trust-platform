import pandas as pd

from src.reports.html_report import (
    build_data_quality_html_report,
)


def test_html_report_accepts_dataset_shape_override():
    html = build_data_quality_html_report(
        file_name="customers.csv",
        file_type="csv",
        df=pd.DataFrame(),
        total_rows=123,
        total_columns=7,
    )

    assert "123" in html
    assert "861" in html


def test_html_report_uses_dataframe_shape_by_default():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        }
    )

    html = build_data_quality_html_report(
        file_name="customers.csv",
        file_type="csv",
        df=df,
    )

    assert "3" in html
    assert "2" in html
    assert "6" in html