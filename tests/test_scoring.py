import pandas as pd
from fastapi.testclient import TestClient

import pytest

from api.main import app
from src.scoring.score_engine import (
    calculate_data_trust_score,
    get_ai_readiness,
    get_risk_level,
)
from src.scoring.weights import SCORE_WEIGHTS
from src.validation.rule_engine import run_quality_checks


client = TestClient(app)


def build_sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": list(range(1, 21)),
            "age": [
                22, 25, 27, 29, 31,
                33, 35, 37, 39, 41,
                43, 45, 47, 49, 51,
                53, 55, 57, 59, 999,
            ],
            "income": [
                500, 520, 510, 530, 540,
                550, 560, 570, 580, 590,
                600, 610, 620, 630, 640,
                650, 660, 670, 680, 50000,
            ],
        }
    )


def test_score_weights_sum_to_one():
    assert sum(SCORE_WEIGHTS.values()) == 1.0


def test_core_risk_thresholds():
    assert get_risk_level(85) == "Low"
    assert get_risk_level(84.99) == "Medium"

    assert get_risk_level(70) == "Medium"
    assert get_risk_level(69.99) == "High"

    assert get_risk_level(50) == "High"
    assert get_risk_level(49.99) == "Critical"


def test_core_ai_readiness_thresholds():
    assert get_ai_readiness(85) == "Ready for Analytics and ML"
    assert get_ai_readiness(70) == "Usable, Minor Cleaning Needed"
    assert get_ai_readiness(50) == "Needs Cleaning Before Training"
    assert get_ai_readiness(49.99) == "Not Ready for AI/ML"


def test_core_score_has_expected_components():
    df = build_sample_dataframe()
    quality_report = run_quality_checks(df)

    result = calculate_data_trust_score(
        df=df,
        quality_report=quality_report,
    )

    assert 0 <= result["overall_score"] <= 100

    assert set(result["score_items"].keys()) == {
        "completeness_score",
        "validity_score",
        "uniqueness_score",
        "consistency_score",
        "anomaly_safety_score",
    }

    assert len(result["breakdown_df"]) == 5


def test_api_score_matches_core_score():
    """
    Contract test:

    FastAPI và core engine phải trả cùng một Trust Score
    cho cùng một dataset.

    Test này bảo vệ nguyên tắc single source of truth:
    API không được tự triển khai scoring logic riêng.
    """
    df = build_sample_dataframe()

    quality_report = run_quality_checks(df)
    core_result = calculate_data_trust_score(
        df=df,
        quality_report=quality_report,
    )

    payload = {
        "file_name": "test_dataset.csv",
        "file_type": "CSV",
        "records": df.to_dict(orient="records"),
    }

    response = client.post(
        "/api/scores/calculate",
        json=payload,
    )

    assert response.status_code == 200

    api_result = response.json()

    assert api_result["overall_score"] == core_result["overall_score"]
    assert api_result["risk_level"] == core_result["risk_level"]
    assert api_result["ai_readiness"] == core_result["ai_readiness"]


def test_api_rejects_empty_records():
    payload = {
        "file_name": "empty_dataset.csv",
        "file_type": "CSV",
        "records": [],
    }

    response = client.post(
        "/api/scores/calculate",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "records must not be empty"


def test_api_components_match_core_breakdown():
    """
    API không chỉ phải khớp overall score,
    mà từng score component cũng phải giống core engine.
    """
    df = build_sample_dataframe()

    quality_report = run_quality_checks(df)
    core_result = calculate_data_trust_score(
        df=df,
        quality_report=quality_report,
    )

    payload = {
        "file_name": "test_dataset.csv",
        "file_type": "CSV",
        "records": df.to_dict(orient="records"),
    }

    response = client.post(
        "/api/scores/calculate",
        json=payload,
    )

    assert response.status_code == 200

    api_components = {
        item["score_name"]: item
        for item in response.json()["components"]
    }

    core_components = {
        str(row["score_name"]): row
        for _, row in core_result["breakdown_df"].iterrows()
    }

    assert set(api_components.keys()) == set(core_components.keys())

    for score_name, core_item in core_components.items():
        api_item = api_components[score_name]

        assert api_item["score"] == pytest.approx(
            float(core_item["score"])
        )
        assert api_item["weight"] == pytest.approx(
            float(core_item["weight"])
        )
        assert api_item["weighted_score"] == pytest.approx(
            float(core_item["weighted_score"])
        )
        assert api_item["raw_value"] == pytest.approx(
            float(core_item["raw_value (%)"])
        )
        assert api_item["detail"] == str(core_item["detail"])