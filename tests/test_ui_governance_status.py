from pathlib import Path


def test_governance_summary_preserves_real_decision():
    from app.ui.governance import build_governance_summary

    result = build_governance_summary({
        "decision": "REJECTED",
        "privacy_status": "CRITICAL",
        "reason": "Privacy risk detected",
        "promotion_eligible": False,
    })

    assert result["decision"] == "REJECTED"
    assert result["privacy_status"] == "CRITICAL"
    assert result["reason"] == "Privacy risk detected"
    assert result["promotion_eligible"] == "NO"


def test_missing_governance_is_not_approved():
    from app.ui.governance import build_governance_summary

    for value in (None, {}):
        result = build_governance_summary(value)
        assert result["decision"] == "Not evaluated"
        assert result["promotion_eligible"] == "Unknown"


def test_trust_score_uses_session_governance():
    source = Path(
        "app/views/4_trust_score.py"
    ).read_text(encoding="utf-8-sig")

    assert "current_governance_result" in source
    assert "build_governance_summary(" in source
