import pandas as pd

from src.profiling.profiler import profile_dataset


def build_profile_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 4],
            "age": [20, 30, None, 40, 40],
            "segment": ["A", "B", "A", "B", "B"],
            "signup_date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                    "2026-01-04",
                    "2026-01-04",
                ]
            ),
            "is_active": [True, False, True, False, False],
            "note": [
                "customer one",
                "customer two",
                "customer three",
                "customer four",
                "customer four",
            ],
        }
    )


def test_profile_returns_expected_sections():
    df = build_profile_dataframe()

    result = profile_dataset(df)

    assert set(result.keys()) == {
        "basic_info",
        "column_types",
        "schema_summary",
        "missing_summary",
        "duplicate_summary",
        "numeric_summary",
        "categorical_summary",
    }


def test_profile_basic_info_counts_correctly():
    df = build_profile_dataframe()

    result = profile_dataset(df)
    basic = result["basic_info"]

    assert basic["total_rows"] == 5
    assert basic["total_columns"] == 6
    assert basic["total_cells"] == 30

    assert basic["missing_cells"] == 1
    assert basic["missing_rate"] == 3.33

    assert basic["duplicate_rows"] == 1
    assert basic["duplicate_rate"] == 20.0


def test_profile_infers_column_types():
    df = build_profile_dataframe()

    result = profile_dataset(df)
    column_types = result["column_types"]

    assert set(column_types["numeric_columns"]) == {
        "customer_id",
        "age",
    }

    assert column_types["categorical_columns"] == [
        "segment",
    ]

    assert column_types["datetime_columns"] == [
        "signup_date",
    ]

    assert column_types["boolean_columns"] == [
        "is_active",
    ]

    assert column_types["text_columns"] == [
        "note",
    ]


def test_profile_missing_summary_and_schema():
    df = build_profile_dataframe()

    result = profile_dataset(df)

    missing_summary = result["missing_summary"]
    schema_summary = result["schema_summary"]

    age_missing = missing_summary[
        missing_summary["column_name"] == "age"
    ].iloc[0]

    assert age_missing["missing_count"] == 1
    assert age_missing["missing_rate (%)"] == 20.0

    age_schema = schema_summary[
        schema_summary["column_name"] == "age"
    ].iloc[0]

    assert age_schema["non_null_count"] == 4
    assert age_schema["null_count"] == 1
    assert age_schema["null_rate (%)"] == 20.0
    assert age_schema["unique_count"] == 3
    assert age_schema["unique_rate (%)"] == 60.0


def test_profile_numeric_and_categorical_summaries():
    df = build_profile_dataframe()

    result = profile_dataset(df)

    numeric_summary = result["numeric_summary"]
    categorical_summary = result["categorical_summary"]

    assert set(numeric_summary["column_name"]) == {
        "customer_id",
        "age",
    }

    age_summary = numeric_summary[
        numeric_summary["column_name"] == "age"
    ].iloc[0]

    assert age_summary["count"] == 4

    assert set(categorical_summary["column_name"]) == {
        "segment",
        "is_active",
        "note",
    }

    segment_summary = categorical_summary[
        categorical_summary["column_name"] == "segment"
    ].iloc[0]

    assert segment_summary["non_null_count"] == 5
    assert segment_summary["null_count"] == 0
    assert segment_summary["unique_count"] == 2


def test_profile_handles_empty_dataframe():
    df = pd.DataFrame()

    result = profile_dataset(df)

    basic = result["basic_info"]

    assert basic["total_rows"] == 0
    assert basic["total_columns"] == 0
    assert basic["total_cells"] == 0
    assert basic["missing_cells"] == 0
    assert basic["missing_rate"] == 0.0
    assert basic["duplicate_rows"] == 0
    assert basic["duplicate_rate"] == 0.0

    assert result["schema_summary"].empty
    assert result["missing_summary"].empty
    assert result["numeric_summary"].empty
    assert result["categorical_summary"].empty

    assert result["column_types"] == {
        "numeric_columns": [],
        "categorical_columns": [],
        "datetime_columns": [],
        "boolean_columns": [],
        "text_columns": [],
    }