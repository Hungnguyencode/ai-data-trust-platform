from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

GOVERNANCE_POLICY_VERSION = "1.0"


@dataclass(frozen=True)
class GovernanceResult:
    decision: str
    reason: str
    promotion_eligible: bool
    policy_version: str
    validation_status: str
    trust_score: float
    privacy_status: str
    blocking_issue_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GovernanceEngine:
    """
    Rule-based governance decision engine.

    Decisions:
    - APPROVED
    - REVIEW_REQUIRED
    - REJECTED
    """

    def __init__(
        self,
        trust_score_threshold: float = 70.0,
    ) -> None:
        self.trust_score_threshold = float(
            trust_score_threshold
        )

    def evaluate(
        self,
        validation_status: str,
        trust_score: float,
        privacy_status: str,
        blocking_issue_count: int = 0,
    ) -> GovernanceResult:
        validation = str(
            validation_status
        ).strip().upper()

        privacy = str(
            privacy_status
        ).strip().upper()

        score = float(
            trust_score
        )

        blocking = int(
            blocking_issue_count
        )

        if not 0 <= score <= 100:
            raise ValueError(
                "trust_score phải nằm trong khoảng 0-100."
            )

        if blocking < 0:
            raise ValueError(
                "blocking_issue_count không được âm."
            )

        if privacy not in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }:
            raise ValueError(
                "privacy_status không hợp lệ: "
                f"{privacy_status}"
            )

        if validation != "ACCEPTED":
            return self._result(
                decision="REJECTED",
                reason=(
                    "Dataset chưa vượt qua Validation Gate."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        if blocking > 0:
            return self._result(
                decision="REJECTED",
                reason=(
                    f"Dataset có {blocking} blocking issue."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        if privacy == "CRITICAL":
            return self._result(
                decision="REJECTED",
                reason=(
                    "Privacy Risk ở mức CRITICAL."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        if privacy == "HIGH":
            return self._result(
                decision="REVIEW_REQUIRED",
                reason=(
                    "Privacy Risk ở mức HIGH; "
                    "cần review trước khi promote."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        if score < self.trust_score_threshold:
            return self._result(
                decision="REVIEW_REQUIRED",
                reason=(
                    "Data Trust Score "
                    f"{score:.2f} thấp hơn ngưỡng "
                    f"{self.trust_score_threshold:.2f}."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        if privacy == "MEDIUM":
            return self._result(
                decision="REVIEW_REQUIRED",
                reason=(
                    "Privacy Risk ở mức MEDIUM; "
                    "cần review trước khi promote."
                ),
                promotion_eligible=False,
                validation_status=validation,
                trust_score=score,
                privacy_status=privacy,
                blocking_issue_count=blocking,
            )

        return self._result(
            decision="APPROVED",
            reason=(
                "Validation, Trust Score và Privacy "
                "đều đạt Governance Policy."
            ),
            promotion_eligible=True,
            validation_status=validation,
            trust_score=score,
            privacy_status=privacy,
            blocking_issue_count=blocking,
        )

    def _result(
        self,
        *,
        decision: str,
        reason: str,
        promotion_eligible: bool,
        validation_status: str,
        trust_score: float,
        privacy_status: str,
        blocking_issue_count: int,
    ) -> GovernanceResult:
        return GovernanceResult(
            decision=decision,
            reason=reason,
            promotion_eligible=promotion_eligible,
            policy_version=GOVERNANCE_POLICY_VERSION,
            validation_status=validation_status,
            trust_score=trust_score,
            privacy_status=privacy_status,
            blocking_issue_count=blocking_issue_count,
        )