import pandas as pd

from src.privacy.pii_detector import (
    _risk_level_from_score,
    _severity_from_pii_type,
    calculate_privacy_safety_score,
    run_privacy_scan,
)


def test_privacy_risk_level_thresholds():
    assert _risk_level_from_score(100.0) == "Low"
    assert _risk_level_from_score(90.0) == "Low"

    assert _risk_level_from_score(89.99) == "Medium"
    assert _risk_level_from_score(75.0) == "Medium"

    assert _risk_level_from_score(74.99) == "High"
    assert _risk_level_from_score(50.0) == "High"

    assert _risk_level_from_score(49.99) == "Critical"
    assert _risk_level_from_score(0.0) == "Critical"


def test_pii_severity_thresholds():
    # High-risk PII types.
    assert _severity_from_pii_type("Email", 19.99) == "Medium"
    assert _severity_from_pii_type("Email", 20.0) == "High"

    assert _severity_from_pii_type("Phone Number", 20.0) == "High"

    # Medium-risk PII types.
    assert _severity_from_pii_type("Full Name", 29.99) == "Medium"
    assert _severity_from_pii_type("Full Name", 30.0) == "High"

    assert _severity_from_pii_type("Address", 30.0) == "High"

    assert _severity_from_pii_type(
        "Unknown Type",
        100.0,
    ) == "Low"


def test_privacy_scan_clean_dataset_is_safe():
    df = pd.DataFrame(
        {
            "product": [
                "Laptop",
                "Mouse",
                "Keyboard",
                "Monitor",
            ],
            "quantity": [1, 2, 3, 4],
        }
    )

    result = run_privacy_scan(df)

    assert set(result.keys()) == {
        "summary",
        "findings_df",
    }

    summary = result["summary"]

    assert summary["total_rows"] == 4
    assert summary["total_columns"] == 2
    assert summary["total_cells"] == 8

    assert summary["pii_columns"] == 0
    assert summary["pii_cells"] == 0
    assert summary["pii_cell_rate (%)"] == 0.0

    assert summary["privacy_safety_score"] == 100.0
    assert summary["risk_level"] == "Low"
    assert summary["high_risk_findings"] == 0

    assert result["findings_df"].empty


def test_privacy_scan_detects_regex_based_pii():
    df = pd.DataFrame(
        {
            # Generic column names are intentional:
            # detection here must come from value patterns,
            # not only from column-name hints.
            "field_a": [
                "alice@example.com",
                "bob@example.com",
                None,
                "not-an-email",
            ],
            "field_b": [
                "0912345678",
                "0987654321",
                None,
                "invalid-phone",
            ],
            "field_c": [
                "123456789012",
                "987654321098",
                None,
                "not-an-id",
            ],
        }
    )

    result = run_privacy_scan(df)
    findings = result["findings_df"]

    detected_types = set(findings["pii_type"])

    assert "Email" in detected_types
    assert "Phone Number" in detected_types
    assert "Citizen ID" in detected_types

    email = findings[
        findings["pii_type"] == "Email"
    ].iloc[0]

    assert email["column_name"] == "field_a"
    assert email["match_count"] == 2
    assert email["match_rate (%)"] == 50.0
    assert email["severity"] == "High"

    phone = findings[
        findings["pii_type"] == "Phone Number"
    ].iloc[0]

    assert phone["column_name"] == "field_b"
    assert phone["match_count"] == 2

    citizen_id = findings[
        findings["pii_type"] == "Citizen ID"
    ].iloc[0]

    assert citizen_id["column_name"] == "field_c"
    assert citizen_id["match_count"] == 2
    assert citizen_id["severity"] == "High"


def test_privacy_scan_uses_column_name_heuristics():
    df = pd.DataFrame(
        {
            "full_name": [
                "Nguyen Van A",
                "Tran Thi B",
                "Le Van C",
                None,
            ],
            "address": [
                "Ha Noi",
                "Da Nang",
                "Hai Phong",
                None,
            ],
        }
    )

    result = run_privacy_scan(df)
    findings = result["findings_df"]

    full_name = findings[
        findings["pii_type"] == "Full Name"
    ].iloc[0]

    assert full_name["column_name"] == "full_name"
    assert full_name["match_count"] == 3
    assert full_name["match_rate (%)"] == 75.0
    assert full_name["severity"] == "High"

    address = findings[
        findings["pii_type"] == "Address"
    ].iloc[0]

    assert address["column_name"] == "address"
    assert address["match_count"] == 3
    assert address["match_rate (%)"] == 75.0
    assert address["severity"] == "High"


def test_privacy_masked_examples_do_not_expose_raw_values():
    raw_email = "alice@example.com"
    raw_phone = "0912345678"

    df = pd.DataFrame(
        {
            "email": [raw_email],
            "phone": [raw_phone],
        }
    )

    result = run_privacy_scan(df)
    findings = result["findings_df"]

    email = findings[
        findings["pii_type"] == "Email"
    ].iloc[0]

    phone = findings[
        findings["pii_type"] == "Phone Number"
    ].iloc[0]

    assert raw_email not in email["masked_examples"]
    assert "***" in email["masked_examples"]

    assert raw_phone not in phone["masked_examples"]
    assert "***" in phone["masked_examples"]
    assert phone["masked_examples"].endswith("5678")


def test_privacy_safety_score_uses_severity_weights():
    findings = pd.DataFrame(
        [
            {
                "severity": "High",
                "match_count": 2,
            },
            {
                "severity": "Medium",
                "match_count": 1,
            },
        ]
    )

    score = calculate_privacy_safety_score(
        pii_findings_df=findings,
        total_cells=10,
    )

    # Weighted risk:
    # High   -> 2 * 1.8 = 3.6
    # Medium -> 1 * 1.0 = 1.0
    # Total  -> 4.6 / 10
    #
    # Score = 100 - 46 = 54
    assert score == 54.0


def test_privacy_scan_detects_vietnamese_phone_formats():
    df = pd.DataFrame(
        {
            "value": [
                "0912345678",
                "0987654321",
                "+84912345678",
                "84987654321",
                "not-a-phone",
            ]
        }
    )

    result = run_privacy_scan(df)

    phone_findings = result["findings_df"][
        result["findings_df"]["pii_type"] == "Phone Number"
    ]

    assert len(phone_findings) == 1

    phone = phone_findings.iloc[0]

    assert phone["column_name"] == "value"
    assert phone["match_count"] == 4
    assert phone["match_rate (%)"] == 80.0
    assert phone["severity"] == "High"