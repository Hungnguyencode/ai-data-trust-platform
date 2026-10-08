from __future__ import annotations

import pandas as pd
import requests

from app.services import report_api


def test_generate_html_report_posts_dataset_shape(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        }
    )

    result = report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
    )

    assert captured["url"] == (
        report_api.HTML_REPORT_URL
    )

    assert captured["json"] == {
        "file_name": "customers.csv",
        "file_type": "csv",
        "total_rows": 3,
        "total_columns": 2,
    }

    assert captured["timeout"] == 15

    assert result == {
        "report_file_name": (
            "data_trust_report.html"
        ),
        "html_content": (
            "<html>report</html>"
        ),
    }


def test_generate_html_report_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "internal network detail"
        )

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    try:
        report_api.generate_html_report(
            df,
            file_name="customers.csv",
            file_type="csv",
        )
    except report_api.ReportApiError as exc:
        assert str(exc) == (
            "Unable to generate HTML report."
        )
        assert (
            "internal network detail"
            not in str(exc)
        )
    else:
        raise AssertionError(
            "ReportApiError was not raised."
        )


def test_generate_html_report_serializes_profile(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
        profile={
            "basic_info": {
                "missing_rate": 1.25,
                "duplicate_rate": 0.5,
            },
        },
    )

    assert captured["json"]["profile"] == {
        "basic_info": {
            "missing_rate": 1.25,
            "duplicate_rate": 0.5,
        },
    }


def test_generate_html_report_serializes_quality_report(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    quality_report = {
        "summary": {
            "total_issues": 2,
            "affected_columns": 1,
        },
        "issues_df": pd.DataFrame(
            [
                {
                    "issue_type": "missing_value",
                    "column_name": "email",
                }
            ]
        ),
    }

    report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
        quality_report=quality_report,
    )

    assert captured["json"]["quality"] == {
        "summary": {
            "total_issues": 2,
            "affected_columns": 1,
        },
        "issue_records": [
            {
                "issue_type": "missing_value",
                "column_name": "email",
            }
        ],
    }


def test_generate_html_report_serializes_trust_score_report(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    trust_score_report = {
        "overall_score": 91.5,
        "risk_level": "Low",
        "ai_readiness": "Ready",
        "conclusion": "Dataset is ready.",
        "breakdown_df": pd.DataFrame(
            [
                {
                    "score_name": "Completeness",
                    "score": 95.0,
                    "weight": 0.25,
                }
            ]
        ),
    }

    report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
        trust_score_report=trust_score_report,
    )

    assert captured["json"]["trust_score"] == {
        "overall_score": 91.5,
        "risk_level": "Low",
        "ai_readiness": "Ready",
        "conclusion": "Dataset is ready.",
        "breakdown_records": [
            {
                "score_name": "Completeness",
                "score": 95.0,
                "weight": 0.25,
            }
        ],
    }


def test_generate_html_report_serializes_privacy_report(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    privacy_report = {
        "summary": {
            "privacy_safety_score": 88.0,
            "risk_level": "Low",
            "pii_columns": 2,
            "pii_cell_rate (%)": 1.5,
        },
        "findings_df": pd.DataFrame(
            [
                {
                    "column_name": "email",
                    "pii_type": "email",
                }
            ]
        ),
    }

    report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
        privacy_report=privacy_report,
    )

    assert captured["json"]["privacy"] == {
        "summary": {
            "privacy_safety_score": 88.0,
            "risk_level": "Low",
            "pii_columns": 2,
            "pii_cell_rate (%)": 1.5,
        },
        "finding_records": [
            {
                "column_name": "email",
                "pii_type": "email",
            }
        ],
    }


def test_generate_html_report_serializes_drift_report(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "html_content": (
                    "<html>report</html>"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
        }
    )

    drift_report = {
        "summary": {
            "drift_score": 18.5,
            "overall_drift_level": "Low",
            "drifted_columns": 1,
            "schema_drift_count": 1,
        },
        "baseline_file_name": (
            "customers_old.csv"
        ),
        "current_file_name": (
            "customers.csv"
        ),
        "numeric_drift_df": pd.DataFrame(
            [
                {
                    "column": "age",
                    "drift_score": 0.12,
                }
            ]
        ),
        "categorical_drift_df": pd.DataFrame(
            [
                {
                    "column": "country",
                    "drift_score": 0.08,
                }
            ]
        ),
        "schema_report": {
            "changes_df": pd.DataFrame(
                [
                    {
                        "change_type": "added_column",
                        "column": "segment",
                    }
                ]
            ),
        },
    }

    report_api.generate_html_report(
        df,
        file_name="customers.csv",
        file_type="csv",
        drift_report=drift_report,
    )

    assert captured["json"]["drift"] == {
        "summary": {
            "drift_score": 18.5,
            "overall_drift_level": "Low",
            "drifted_columns": 1,
            "schema_drift_count": 1,
        },
        "baseline_file_name": (
            "customers_old.csv"
        ),
        "current_file_name": (
            "customers.csv"
        ),
        "numeric_drift_records": [
            {
                "column": "age",
                "drift_score": 0.12,
            }
        ],
        "categorical_drift_records": [
            {
                "column": "country",
                "drift_score": 0.08,
            }
        ],
        "schema_change_records": [
            {
                "change_type": "added_column",
                "column": "segment",
            }
        ],
    }


def test_save_html_report_posts_save_command(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "report_file_name": (
                    "data_trust_report.html"
                ),
                "saved_path": (
                    "data/reports/"
                    "data_trust_report.html"
                ),
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    result = report_api.save_html_report(
        html_content="<html>report</html>",
        report_file_name=(
            "data_trust_report.html"
        ),
    )

    assert captured["url"] == (
        report_api.SAVE_HTML_REPORT_URL
    )

    assert captured["json"] == {
        "html_content": "<html>report</html>",
        "report_file_name": (
            "data_trust_report.html"
        ),
    }

    assert captured["timeout"] == 15

    assert result == {
        "report_file_name": (
            "data_trust_report.html"
        ),
        "saved_path": (
            "data/reports/"
            "data_trust_report.html"
        ),
    }


def test_save_html_report_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "internal network detail"
        )

    monkeypatch.setattr(
        report_api.requests,
        "post",
        fake_post,
    )

    try:
        report_api.save_html_report(
            html_content="<html>report</html>",
            report_file_name=(
                "data_trust_report.html"
            ),
        )
    except report_api.ReportApiError as exc:
        assert str(exc) == (
            "Unable to save HTML report."
        )
        assert (
            "internal network detail"
            not in str(exc)
        )
    else:
        raise AssertionError(
            "ReportApiError was not raised."
        )