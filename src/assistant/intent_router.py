from __future__ import annotations

import re
import unicodedata
from typing import Dict, List


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa câu hỏi để router hiểu được cả tiếng Việt có dấu/không dấu.
    Ví dụ:
    - "Tại sao điểm thấp?" -> "tai sao diem thap"
    - "Sửa missing value như thế nào?" -> "sua missing value nhu the nao"
    """

    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9_/%.\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _contains_any(text: str, patterns: List[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def detect_intent(question: str) -> Dict[str, object]:
    """
    Intent router Version 2.5.

    Trả về:
    - intent: tên ý định
    - confidence: mức tự tin tương đối
    - matched_group: nhóm rule bắt được

    Rule được xếp theo độ cụ thể trước, câu hỏi chung sau.
    """

    q = normalize_text(question)

    if not q:
        return {
            "intent": "empty",
            "confidence": 1.0,
            "matched_group": "empty",
            "normalized_question": q,
        }

    # 1. Public/share/GitHub decision
    if _contains_any(
        q,
        [
            "co nen public",
            "co public duoc khong",
            "dataset nay co nen public",
            "cong khai",
            "chia se",
            "share dataset",
            "dua len github",
            "upload github",
            "public dataset",
            "co nen chia se",
            "co nen dua len github",
            "up github",
            "up len github",
            "day len github",
            "dua github",
            "github",
            "repo",
            "repository",
            "public len github",
            "upload len github",
            "co nen up",
            "co nen day len",
        ],
    ):
        return {
            "intent": "public_dataset_decision",
            "confidence": 0.95,
            "matched_group": "public_or_share",
            "normalized_question": q,
        }

    # 2. Cleaning plan theo từng cột
    if _contains_any(
        q,
        [
            "cleaning plan",
            "clean plan",
            "ke hoach lam sach",
            "ke hoach xu ly",
            "lap ke hoach xu ly",
            "lap bang xu ly",
            "bang xu ly",
            "bang cleaning",
            "xu ly theo tung cot",
            "lam sach theo tung cot",
            "clean theo tung cot",
            "cot nao sua nhu the nao",
            "moi cot sua nhu the nao",
            "giai phap tung cot",
            "de xuat xu ly tung cot",
            "sua tung cot",
            "xu ly tung cot",
            "data cleaning plan",
            "cleaning theo cot",
            "clean dataset nhu the nao",
            "lam sach dataset nhu the nao",
        ],
    ):
        return {
            "intent": "cleaning_plan",
            "confidence": 0.95,
            "matched_group": "cleaning_plan",
            "normalized_question": q,
        }

    # 9. Column priority
    if _contains_any(
        q,
        [
            "cot nao nen xu ly",
            "cot nao can xu ly",
            "xu ly cot nao truoc",
            "cot nao nguy hiem",
            "cot nao loi nhieu",
            "column nao",
            "uu tien cot",
            "cot uu tien",
            "cot can sua",
            "cot nao nguy hiem nhat",
            "cot nao dang lo nhat",
            "cot nao rui ro nhat",
            "cot nao bi loi nang nhat",
            "cot nao can uu tien",
                    ],
    ):
        return {
            "intent": "explain_top_columns_to_fix",
            "confidence": 0.95,
            "matched_group": "top_columns",
            "normalized_question": q,
        }

    # 2. Biggest risk
    if _contains_any(
        q,
        [
            "rui ro lon nhat",
            "van de lon nhat",
            "loi lon nhat",
            "dang lo nhat",
            "nguy hiem nhat",
            "biggest risk",
            "main risk",
            "risk lon nhat",
            "dieu dang lo",
        ],
    ):
        return {
            "intent": "biggest_risk_summary",
            "confidence": 0.95,
            "matched_group": "biggest_risk",
            "normalized_question": q,
        }

    # 3. Score gap / why score is not high
    if _contains_any(
        q,
        [
            "tai sao trust score",
            "vi sao trust score",
            "tai sao diem",
            "vi sao diem",
            "diem thap",
            "score thap",
            "score chua cao",
            "diem chua cao",
            "chua dat 90",
            "khong dat 90",
            "tai sao chi duoc",
            "vi sao chi duoc",
            "tai sao dat",
            "vi sao dat",
            "keo diem xuong",
            "nhom nao keo diem",
            "sao trust",
            "sao trusting",
            "trusting score",
            "chi co 86",
            "chi duoc 86",
            "moi co 86",
            "vi sao chi co",
            "sao chi co",
            "tai sao chi co",
            "sao diem chi",
            "sao score chi",
            "diem moi",
            "score moi",
        ],
    ):
        return {
            "intent": "explain_score_gap",
            "confidence": 0.95,
            "matched_group": "score_gap",
            "normalized_question": q,
        }

    # 4. Missing value
    if _contains_any(
        q,
        [
            "missing",
            "missing value",
            "gia tri thieu",
            "du lieu thieu",
            "thieu du lieu",
            "cot nao bi thieu",
            "sua missing",
            "xu ly missing",
            "fix missing",
            "fillna",
            "dien gia tri thieu",
            "dien missing",
        ],
    ):
        return {
            "intent": "explain_missing_fix",
            "confidence": 0.95,
            "matched_group": "missing",
            "normalized_question": q,
        }

    # 5. Duplicate rows
    if _contains_any(
        q,
        [
            "duplicate",
            "duplicates",
            "trung lap",
            "dong trung",
            "trung dong",
            "sua duplicate",
            "xu ly duplicate",
            "drop duplicate",
            "drop_duplicates",
            "ban ghi trung",
        ],
    ):
        return {
            "intent": "explain_duplicate_fix",
            "confidence": 0.95,
            "matched_group": "duplicate",
            "normalized_question": q,
        }

    # 6. Outlier/anomaly decision
    if _contains_any(
        q,
        [
            "outlier co nen xoa",
            "co nen xoa outlier",
            "xoa outlier",
            "xu ly outlier",
            "outlier",
            "anomaly co nen xoa",
            "dong bat thuong co nen xoa",
            "bat thuong co nen xoa",
            "co nen xoa dong bat thuong",
            "gia tri bat thuong",
        ],
    ):
        return {
            "intent": "explain_outlier_decision",
            "confidence": 0.95,
            "matched_group": "outlier_decision",
            "normalized_question": q,
        }

    # 7. Drift decision
    if _contains_any(
        q,
        [
            "drift cao",
            "data drift cao",
            "co drift",
            "current dataset",
            "dung current",
            "co dung current",
            "thay baseline",
            "current thay baseline",
            "baseline current",
            "phan phoi thay doi",
            "co nen dung current",
            "current bi drift",
            "bi drift",
            "drift thi co dung duoc khong",
            "co dung duoc khong",
            "drift co dung duoc khong",
            "current drift co dung duoc khong",
            "current co dung duoc khong",
            "du lieu current co dung duoc khong",
            "current bi drift thi co dung",
        ],
    ):
        return {
            "intent": "explain_drift_decision",
            "confidence": 0.95,
            "matched_group": "drift_decision",
            "normalized_question": q,
        }

    # 8. Privacy high reason
    if _contains_any(
        q,
        [
            "privacy high",
            "privacy risk high",
            "vi sao privacy",
            "tai sao privacy",
            "vi sao privacy risk",
            "tai sao privacy risk",
            "rui ro rieng tu cao",
            "rieng tu cao",
            "pii nguy hiem",
            "du lieu nhay cam nguy hiem",
        ],
    ):
        return {
            "intent": "explain_privacy_high_reason",
            "confidence": 0.95,
            "matched_group": "privacy_high_reason",
            "normalized_question": q,
        }

    # 10. Fast score improvement
    if _contains_any(
        q,
        [
            "tang diem",
            "tang score",
            "cai thien diem",
            "cai thien score",
            "keo diem len",
            "keo score len",
            "muon tang diem",
            "sua gi de tang diem",
            "lam sao dat 90",
            "lam sao len 90",
            "dat 90",
            "len 90",
        ],
    ):
        return {
            "intent": "fast_score_improvement_plan",
            "confidence": 0.95,
            "matched_group": "score_improvement",
            "normalized_question": q,
        }

    # 11. Priority action plan
    if _contains_any(
        q,
        [
            "sua gi truoc",
            "fix gi truoc",
            "xu ly gi truoc",
            "nen sua gi truoc",
            "uu tien",
            "3 van de",
            "ba van de",
            "ke hoach xu ly",
            "action plan",
            "priority plan",
            "nen lam gi truoc",
        ],
    ):
        return {
            "intent": "priority_action_plan",
            "confidence": 0.9,
            "matched_group": "priority_plan",
            "normalized_question": q,
        }

    # 12. Smart diagnosis / overall assessment
    if _contains_any(
        q,
        [
            "dataset co on khong",
            "du lieu co on khong",
            "on khong",
            "danh gia tong the",
            "nhan xet tong the",
            "chan doan",
            "diagnosis",
            "tong quan van de",
            "chat luong the nao",
            "project nay on khong",
        ],
    ):
        return {
            "intent": "smart_diagnosis",
            "confidence": 0.9,
            "matched_group": "overall_diagnosis",
            "normalized_question": q,
        }

    # 13. AI readiness
    if _contains_any(
        q,
        [
            "ai readiness",
            "san sang cho ai",
            "san sang cho ml",
            "ready for ml",
            "ready for ai",
            "machine learning",
            "ai/ml",
            "co train duoc khong",
            "co dung cho model duoc khong",
            "huan luyen mo hinh",
            "training model",
            "train model",
            "training duoc khong",
            "train duoc khong",
            "model duoc chua",
            "du lieu nay train",
            "dataset nay train",
            "co train model duoc khong",
            "co dung train model duoc khong",
            "co dung de train duoc khong",
            "co dung de train model duoc khong",
        ],
    ):
        return {
            "intent": "ai_readiness_explanation",
            "confidence": 0.9,
            "matched_group": "ai_readiness",
            "normalized_question": q,
        }

    # 14. Trust score summary
    if _contains_any(
        q,
        [
            "trust score",
            "data trust",
            "score",
            "diem",
            "diem tong",
            "diem tin cay",
            "risk level",
        ],
    ):
        return {
            "intent": "trust_score_summary",
            "confidence": 0.8,
            "matched_group": "trust_score_general",
            "normalized_question": q,
        }

    # 15. Quality summary
    if _contains_any(
        q,
        [
            "quality",
            "quality issues",
            "loi du lieu",
            "issue",
            "issues",
            "validity",
            "range",
            "kieu du lieu",
            "invalid",
            "categorical",
        ],
    ):
        return {
            "intent": "quality_summary",
            "confidence": 0.8,
            "matched_group": "quality_general",
            "normalized_question": q,
        }

    # 16. Anomaly summary
    if _contains_any(
        q,
        [
            "anomaly",
            "bat thuong",
            "iqr",
            "z-score",
            "zscore",
            "isolation forest",
            "outlier summary",
        ],
    ):
        return {
            "intent": "anomaly_summary",
            "confidence": 0.8,
            "matched_group": "anomaly_general",
            "normalized_question": q,
        }

    # 17. Privacy summary
    if _contains_any(
        q,
        [
            "privacy",
            "pii",
            "nhay cam",
            "rieng tu",
            "email",
            "phone",
            "sdt",
            "cccd",
            "cmnd",
            "address",
            "dia chi",
            "name",
            "ten",
        ],
    ):
        return {
            "intent": "privacy_summary",
            "confidence": 0.8,
            "matched_group": "privacy_general",
            "normalized_question": q,
        }

    # 18. Drift summary
    if _contains_any(
        q,
        [
            "drift",
            "baseline",
            "current",
            "psi",
            "ks-test",
            "schema drift",
            "data drift",
            "categorical drift",
            "numeric drift",
            "phan phoi",
        ],
    ):
        return {
            "intent": "drift_summary",
            "confidence": 0.8,
            "matched_group": "drift_general",
            "normalized_question": q,
        }

    # 19. Dataset summary
    if _contains_any(
        q,
        [
            "dataset",
            "du lieu hien tai",
            "file hien tai",
            "tom tat dataset",
            "tong quan dataset",
            "file nay",
            "du lieu nay",
            "bao nhieu dong",
            "bao nhieu cot",
        ],
    ):
        return {
            "intent": "dataset_summary",
            "confidence": 0.75,
            "matched_group": "dataset_general",
            "normalized_question": q,
        }

    return {
        "intent": "out_of_scope",
        "confidence": 0.0,
        "matched_group": "none",
        "normalized_question": q,
    }


def get_intent_debug_text(question: str) -> str:
    result = detect_intent(question)
    return (
        f"intent={result['intent']}, "
        f"confidence={result['confidence']}, "
        f"group={result['matched_group']}"
    )