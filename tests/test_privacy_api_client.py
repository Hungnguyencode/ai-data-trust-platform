import pandas as pd
import requests

from app.services import privacy_api


def test_run_privacy_scan_reconstructs_findings_dataframe(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "summary": {
                    "total_rows": 2,
                    "total_columns": 2,
                    "total_cells": 4,
                    "pii_columns": 1,
                    "pii_cells": 2,
                    "pii_cell_rate (%)": 50.0,
                    "privacy_safety_score": 50.0,
                    "risk_level": "High",
                    "high_risk_findings": 1,
                },
                "findings_records": [
                    {
                        "column_name": "email",
                        "pii_type": "Email",
                        "match_count": 2,
                        "match_rate (%)": 100.0,
                        "severity": "High",
                        "masked_examples": "***@example.com",
                    }
                ],
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
        privacy_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        [
            {
                "name": "Nguyen Van A",
                "email": "alice@example.com",
            },
            {
                "name": "Tran Thi B",
                "email": "bob@example.com",
            },
        ]
    )

    result = privacy_api.run_privacy_scan(
        dataframe
    )

    assert captured["url"].endswith(
        "/api/privacy/scan"
    )

    assert captured["json"] == {
        "records": [
            {
                "name": "Nguyen Van A",
                "email": "alice@example.com",
            },
            {
                "name": "Tran Thi B",
                "email": "bob@example.com",
            },
        ]
    }

    assert result["summary"][
        "total_rows"
    ] == 2

    assert isinstance(
        result["findings_df"],
        pd.DataFrame,
    )

    assert len(
        result["findings_df"]
    ) == 1


def test_run_privacy_scan_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        privacy_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        {
            "email": [
                "alice@example.com",
            ]
        }
    )

    try:
        privacy_api.run_privacy_scan(
            dataframe
        )
    except privacy_api.PrivacyApiError as exc:
        assert str(exc) == (
            "Unable to run privacy scan."
        )
    else:
        raise AssertionError(
            "Expected PrivacyApiError"
        )