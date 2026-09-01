from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.governance.governance_engine import (
    GovernanceEngine,
    GovernanceResult,
)
from src.privacy.pii_detector import run_privacy_scan
from src.scoring.score_engine import (
    calculate_data_trust_score,
)
from src.validation.rule_engine import (
    run_quality_checks,
)


def evaluate_dataset_governance(
    *,
    df: pd.DataFrame,
    validation_result: Mapping[str, Any],
    engine: GovernanceEngine | None = None,
) -> dict[str, Any]:
    if df.empty:
        raise ValueError(
            "Không thể governance dataset rỗng."
        )

    validation = dict(
        validation_result
    )

    if "status" not in validation:
        raise ValueError(
            "validation_result thiếu status."
        )

    quality_report = run_quality_checks(
        df
    )

    trust_score_report = (
        calculate_data_trust_score(
            df=df,
            quality_report=quality_report,
        )
    )

    privacy_report = run_privacy_scan(
        df
    )

    governance_engine = (
        engine
        if engine is not None
        else GovernanceEngine()
    )

    result: GovernanceResult = (
        governance_engine.evaluate(
            validation_status=str(
                validation["status"]
            ),
            trust_score=float(
                trust_score_report[
                    "overall_score"
                ]
            ),
            privacy_status=str(
                privacy_report[
                    "summary"
                ][
                    "risk_level"
                ]
            ),
            blocking_issue_count=int(
                validation.get(
                    "blocking_issue_count",
                    0,
                )
            ),
        )
    )

    return {
        "governance_result": result,
        "quality_report": quality_report,
        "trust_score_report": (
            trust_score_report
        ),
        "privacy_report": privacy_report,
    }