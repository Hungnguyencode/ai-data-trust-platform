from types import SimpleNamespace

import pandas as pd

from api.routes import workflows


def test_workflow_response_serializes_nested_dataframe(monkeypatch):
    summary = {
        "ingestion_id": "test-ingestion",
        "catalog_id": 1,
        "version_id": 2,
        "version_number": 1,
        "validation_id": 3,
        "validation_status": "PASSED",
        "governance_id": 4,
        "governance_decision": "ALLOW",
        "trust_score": 95.0,
        "privacy_status": "OK",
        "lifecycle_state": "DRAFT",
        "promotion_eligible": False,
    }

    result = SimpleNamespace(
        summary=lambda: summary,
        dataframe=pd.DataFrame({"id": [1]}),
        profile=None,
        ingestion_metadata={},
        catalog_registration={},
        validation_result={},
        validation_registration={},
        governance_result={},
        governance_registration={},
        lifecycle_result={},
        quality_report={
            "by_column": pd.DataFrame({
                "column": ["id"],
                "missing": [0],
            })
        },
        trust_score_report={},
        privacy_report={},
        data_contract=None,
        contract_validation=None,
    )

    monkeypatch.setattr(
        workflows,
        "_serialize_profile",
        lambda _: {},
    )

    response = workflows._build_workflow_response(result)
    payload = response.model_dump(mode="json")

    assert payload["quality_report"]["by_column"] == [
        {"column": "id", "missing": 0}
    ]
