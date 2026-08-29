from __future__ import annotations

from typing import Any, Callable, Dict

from src.assistant.cleaning_plan import cleaning_plan_markdown
from src.assistant.fallback_rules import (
    ai_readiness_explanation,
    anomaly_summary,
    biggest_risk_summary,
    dataset_summary,
    drift_summary,
    explain_drift_decision,
    explain_duplicate_fix,
    explain_missing_fix,
    explain_outlier_decision,
    explain_privacy_high_reason,
    explain_score_gap,
    explain_top_columns_to_fix,
    fast_score_improvement_plan,
    priority_action_plan,
    privacy_summary,
    public_dataset_decision,
    quality_summary,
    smart_diagnosis,
    trust_score_summary,
)
from src.assistant.intent_router import detect_intent

ASSISTANT_VERSION = "2.6"


def _missing_message(section_name: str, tab_name: str) -> str:
    return (
        f"Chưa có kết quả **{section_name}** trong session hiện tại. "
        f"Hãy chạy tab **{tab_name}** trước, sau đó hỏi lại assistant."
    )


def _out_of_scope_answer() -> str:
    return """
Mình chỉ trả lời dựa trên kết quả scan hiện có trong hệ thống.

Bạn có thể hỏi theo các nhóm sau:

- Dataset hiện tại có gì?
- Vì sao Trust Score thấp/chưa đạt 90?
- Nên sửa lỗi nào trước?
- Sửa missing value như thế nào?
- Sửa duplicate rows như thế nào?
- Outlier có nên xóa không?
- Privacy Risk đang nguy hiểm ở đâu?
- Drift cao thì có dùng current dataset được không?
- Dataset này có nên public không?
- Muốn tăng điểm nhanh nhất thì sửa gì?
- Lập cleaning plan theo từng cột?

Nếu câu hỏi nằm ngoài kết quả scan, mình sẽ không tự bịa thêm dữ liệu.
""".strip()


def _safe_context_section(context: Dict[str, Any], section: str) -> Dict[str, Any]:
    value = context.get(section, {})

    if isinstance(value, dict):
        return value

    return {}


def _has_context(context: Dict[str, Any], section: str) -> bool:
    value = _safe_context_section(context, section)
    return bool(value)


def _has_any_cleaning_context(context: Dict[str, Any]) -> bool:
    """
    Cleaning plan có thể dùng nhiều nguồn scan khác nhau.
    Chỉ cần có ít nhất 1 trong 4 nhóm này là có thể sinh plan:
    - quality
    - privacy
    - anomaly
    - drift
    """
    return any(
        [
            _has_context(context, "quality"),
            _has_context(context, "privacy"),
            _has_context(context, "anomaly"),
            _has_context(context, "drift"),
        ]
    )


def _build_intent_handlers() -> Dict[str, Callable[[Dict[str, Any]], str]]:
    return {
        "public_dataset_decision": public_dataset_decision,
        "biggest_risk_summary": biggest_risk_summary,
        "explain_score_gap": explain_score_gap,
        "explain_missing_fix": explain_missing_fix,
        "explain_duplicate_fix": explain_duplicate_fix,
        "explain_outlier_decision": explain_outlier_decision,
        "explain_drift_decision": explain_drift_decision,
        "explain_privacy_high_reason": explain_privacy_high_reason,
        "explain_top_columns_to_fix": explain_top_columns_to_fix,
        "fast_score_improvement_plan": fast_score_improvement_plan,
        "priority_action_plan": priority_action_plan,
        "smart_diagnosis": smart_diagnosis,
        "dataset_summary": dataset_summary,
        "trust_score_summary": trust_score_summary,
        "quality_summary": quality_summary,
        "anomaly_summary": anomaly_summary,
        "privacy_summary": privacy_summary,
        "drift_summary": drift_summary,
        "ai_readiness_explanation": ai_readiness_explanation,
        "cleaning_plan": cleaning_plan_markdown,
    }


def _check_required_context(intent: str, context: Dict[str, Any]) -> str | None:
    trust_intents = {
        "trust_score_summary",
        "explain_score_gap",
        "fast_score_improvement_plan",
        "ai_readiness_explanation",
    }

    quality_intents = {
        "quality_summary",
        "explain_missing_fix",
        "explain_duplicate_fix",
        "priority_action_plan",
        "explain_top_columns_to_fix",
    }

    anomaly_intents = {
        "anomaly_summary",
        "explain_outlier_decision",
    }

    privacy_intents = {
        "privacy_summary",
        "explain_privacy_high_reason",
        "public_dataset_decision",
    }

    drift_intents = {
        "drift_summary",
        "explain_drift_decision",
    }

    if intent in trust_intents and not _has_context(context, "trust_score"):
        return _missing_message("Trust Score", "Trust Score")

    if intent in quality_intents and not _has_context(context, "quality"):
        return _missing_message("Quality Issues", "Quality Issues")

    if intent in anomaly_intents and not _has_context(context, "anomaly"):
        return _missing_message("Anomaly Detection", "Anomaly Detection")

    if intent in privacy_intents and not _has_context(context, "privacy"):
        return _missing_message("Privacy Risk", "Privacy Risk")

    if intent in drift_intents and not _has_context(context, "drift"):
        return _missing_message("Drift Detection", "Drift Analysis")

    if intent == "cleaning_plan" and not _has_any_cleaning_context(context):
        return (
            "Chưa có đủ kết quả scan để lập **Cleaning Plan**. "
            "Hãy chạy ít nhất một trong các tab: **Quality Issues**, "
            "**Privacy Risk**, **Anomaly Detection** hoặc **Drift Analysis**."
        )

    return None


def answer_question(question: str, context: Dict[str, Any]) -> str:
    """
    Rule-grounded assistant Version 2.6.

    Nguyên tắc:
    - Chỉ trả lời dựa trên scan context.
    - Không tự bịa dữ liệu ngoài context.
    - Dùng intent router để hiểu nhiều cách hỏi tự nhiên hơn.
    - Có thể sinh cleaning plan theo từng cột từ quality/privacy/anomaly/drift.
    - Không hiển thị metadata kỹ thuật ra giao diện người dùng.
    """

    clean_question = str(question or "").strip()

    if not clean_question:
        return "Bạn cần nhập câu hỏi trước."

    safe_context = context if isinstance(context, dict) else {}

    try:
        router_result = detect_intent(clean_question)
        intent = str(router_result.get("intent", "out_of_scope"))
    except Exception:
        intent = "out_of_scope"

    if intent == "empty":
        return "Bạn cần nhập câu hỏi trước."

    missing_message = _check_required_context(intent, safe_context)

    if missing_message:
        return missing_message

    intent_handlers = _build_intent_handlers()
    handler = intent_handlers.get(intent)

    if handler is None:
        return _out_of_scope_answer()

    try:
        answer = handler(safe_context)
    except Exception as exc:
        return (
            "Assistant gặp lỗi khi đọc kết quả scan hiện tại. "
            f"Chi tiết lỗi: `{exc}`"
        )

    return answer


def generate_quick_insight(topic: str, context: Dict[str, Any]) -> str:
    clean_topic = str(topic or "").strip().lower()
    safe_context = context if isinstance(context, dict) else {}

    mapping: Dict[str, Callable[[Dict[str, Any]], str]] = {
        "dataset": dataset_summary,
        "trust score": trust_score_summary,
        "quality": quality_summary,
        "anomaly": anomaly_summary,
        "privacy": privacy_summary,
        "drift": drift_summary,
        "recommendations": priority_action_plan,
        "smart diagnosis": smart_diagnosis,
        "ai readiness": ai_readiness_explanation,
        "cleaning plan": cleaning_plan_markdown,
    }

    func = mapping.get(clean_topic)

    if func is None:
        return "Không tìm thấy quick insight phù hợp."

    try:
        return func(safe_context)
    except Exception as exc:
        return f"Không thể tạo quick insight cho mục này. Chi tiết lỗi: `{exc}`"