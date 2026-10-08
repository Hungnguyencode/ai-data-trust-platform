from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.reports as report_route
from api.main import app

client = TestClient(app)


def test_generate_html_report_returns_report():
    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["report_file_name"].endswith(
        ".html"
    )
    assert "123" in payload["html_content"]
    assert "861" in payload["html_content"]


def test_generate_html_report_reconstructs_quality_evidence(
    monkeypatch,
):
    captured = {}

    def fake_build_report(**kwargs):
        captured.update(kwargs)
        return "<html>quality report</html>"

    monkeypatch.setattr(
        report_route,
        "build_data_quality_html_report",
        fake_build_report,
    )

    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
            "quality": {
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
            },
        },
    )

    assert response.status_code == 200

    quality_report = captured[
        "quality_report"
    ]

    assert quality_report["summary"] == {
        "total_issues": 2,
        "affected_columns": 1,
    }

    assert (
        quality_report["issues_df"]
        .to_dict(orient="records")
        == [
            {
                "issue_type": "missing_value",
                "column_name": "email",
            }
        ]
    )


def test_generate_html_report_reconstructs_trust_score_evidence(
    monkeypatch,
):
    captured = {}

    def fake_build_report(**kwargs):
        captured.update(kwargs)
        return "<html>trust report</html>"

    monkeypatch.setattr(
        report_route,
        "build_data_quality_html_report",
        fake_build_report,
    )

    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
            "trust_score": {
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
            },
        },
    )

    assert response.status_code == 200

    trust_score_report = captured[
        "trust_score_report"
    ]

    assert trust_score_report[
        "overall_score"
    ] == 91.5

    assert trust_score_report[
        "risk_level"
    ] == "Low"

    assert trust_score_report[
        "ai_readiness"
    ] == "Ready"

    assert trust_score_report[
        "conclusion"
    ] == "Dataset is ready."

    assert (
        trust_score_report["breakdown_df"]
        .to_dict(orient="records")
        == [
            {
                "score_name": "Completeness",
                "score": 95.0,
                "weight": 0.25,
            }
        ]
    )


def test_generate_html_report_reconstructs_privacy_evidence(
    monkeypatch,
):
    captured = {}

    def fake_build_report(**kwargs):
        captured.update(kwargs)
        return "<html>privacy report</html>"

    monkeypatch.setattr(
        report_route,
        "build_data_quality_html_report",
        fake_build_report,
    )

    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
            "privacy": {
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
            },
        },
    )

    assert response.status_code == 200

    privacy_report = captured[
        "privacy_report"
    ]

    assert privacy_report["summary"] == {
        "privacy_safety_score": 88.0,
        "risk_level": "Low",
        "pii_columns": 2,
        "pii_cell_rate (%)": 1.5,
    }

    assert (
        privacy_report["findings_df"]
        .to_dict(orient="records")
        == [
            {
                "column_name": "email",
                "pii_type": "email",
            }
        ]
    )


def test_generate_html_report_reconstructs_drift_evidence(
    monkeypatch,
):
    captured = {}

    def fake_build_report(**kwargs):
        captured.update(kwargs)
        return "<html>drift report</html>"

    monkeypatch.setattr(
        report_route,
        "build_data_quality_html_report",
        fake_build_report,
    )

    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
            "drift": {
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
            },
        },
    )

    assert response.status_code == 200

    drift_report = captured[
        "drift_report"
    ]

    assert drift_report["summary"] == {
        "drift_score": 18.5,
        "overall_drift_level": "Low",
        "drifted_columns": 1,
        "schema_drift_count": 1,
    }

    assert (
        drift_report["baseline_file_name"]
        == "customers_old.csv"
    )

    assert (
        drift_report["current_file_name"]
        == "customers.csv"
    )

    assert (
        drift_report["numeric_drift_df"]
        .to_dict(orient="records")
        == [
            {
                "column": "age",
                "drift_score": 0.12,
            }
        ]
    )

    assert (
        drift_report["categorical_drift_df"]
        .to_dict(orient="records")
        == [
            {
                "column": "country",
                "drift_score": 0.08,
            }
        ]
    )

    assert (
        drift_report["schema_report"][
            "changes_df"
        ]
        .to_dict(orient="records")
        == [
            {
                "change_type": "added_column",
                "column": "segment",
            }
        ]
    )


def test_generate_html_report_reconstructs_profile_evidence(
    monkeypatch,
):
    captured = {}

    def fake_build_report(**kwargs):
        captured.update(kwargs)
        return "<html>profile report</html>"

    monkeypatch.setattr(
        report_route,
        "build_data_quality_html_report",
        fake_build_report,
    )

    response = client.post(
        "/api/reports/html",
        json={
            "file_name": "customers.csv",
            "file_type": "csv",
            "total_rows": 123,
            "total_columns": 7,
            "profile": {
                "basic_info": {
                    "missing_rate": 1.25,
                    "duplicate_rate": 0.5,
                },
            },
        },
    )

    assert response.status_code == 200

    assert captured["profile"] == {
        "basic_info": {
            "missing_rate": 1.25,
            "duplicate_rate": 0.5,
        },
    }


def test_save_html_report_uses_server_reports_directory(
    monkeypatch,
):
    captured = {}

    def fake_save_html_report(
        html_content,
        output_dir,
        file_name,
    ):
        captured["html_content"] = html_content
        captured["output_dir"] = output_dir
        captured["file_name"] = file_name

        return output_dir / file_name

    monkeypatch.setattr(
        report_route,
        "save_html_report",
        fake_save_html_report,
        raising=False,
    )

    response = client.post(
        "/api/reports/html/save",
        json={
            "html_content": "<html>report</html>",
            "report_file_name": (
                "data_trust_report_20261007.html"
            ),
        },
    )

    assert response.status_code == 200

    assert captured["html_content"] == (
        "<html>report</html>"
    )

    assert captured["output_dir"] == (
        report_route.REPORTS_DIR
    )

    assert captured["file_name"] == (
        "data_trust_report_20261007.html"
    )

    assert response.json() == {
        "report_file_name": (
            "data_trust_report_20261007.html"
        ),
        "saved_path": str(
            report_route.REPORTS_DIR
            / "data_trust_report_20261007.html"
        ),
    }


def test_save_html_report_rejects_path_traversal(
    monkeypatch,
):
    def fake_save_html_report(*args, **kwargs):
        raise AssertionError(
            "save_html_report must not be called"
        )

    monkeypatch.setattr(
        report_route,
        "save_html_report",
        fake_save_html_report,
    )

    response = client.post(
        "/api/reports/html/save",
        json={
            "html_content": "<html>report</html>",
            "report_file_name": "../outside.html",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Invalid report file name."
    }


def test_save_html_report_rejects_windows_path_traversal(
    monkeypatch,
):
    def fake_save_html_report(*args, **kwargs):
        raise AssertionError(
            "save_html_report must not be called"
        )

    monkeypatch.setattr(
        report_route,
        "save_html_report",
        fake_save_html_report,
    )

    response = client.post(
        "/api/reports/html/save",
        json={
            "html_content": "<html>report</html>",
            "report_file_name": (
                r"..\outside.html"
            ),
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Invalid report file name."
    }