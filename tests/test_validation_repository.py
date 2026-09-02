from database.repositories.validation_repository import (
    build_rejection_reason,
)


def test_accepted_validation_has_no_rejection_reason():
    result = {
        "status": "ACCEPTED",
        "blocking_issues": [],
    }

    assert (
        build_rejection_reason(
            result
        )
        is None
    )


def test_rejected_validation_builds_reason():
    result = {
        "status": "REJECTED",
        "blocking_issues": [
            {
                "issue_type": "Missing Value",
                "column_name": "age",
                "severity": "High",
            }
        ],
    }

    reason = build_rejection_reason(
        result
    )

    assert reason is not None
    assert "Missing Value" in reason
    assert "age" in reason
    assert "High" in reason


def test_rejected_validation_has_fallback_reason():
    result = {
        "status": "REJECTED",
        "blocking_issues": [],
    }

    reason = build_rejection_reason(
        result
    )

    assert reason is not None
    assert "Validation Gate" in reason