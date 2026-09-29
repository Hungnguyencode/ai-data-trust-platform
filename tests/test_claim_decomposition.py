from src.assistant.claim_decomposition import (
    split_claim_segments,
)


def test_split_claim_segments_keeps_internal_then_in_same_claim():
    question = (
        "Explain what happens if volume "
        "drops then recovers."
    )

    assert split_claim_segments(
        question
    ) == [
        question,
    ]


def test_split_claim_segments_splits_then_before_known_claim_starter():
    assert split_claim_segments(
        (
            "Compare volume over time "
            "then tell me the latest volume."
        )
    ) == [
        "Compare volume over time",
        "tell me the latest volume.",
    ]


def test_split_claim_segments_keeps_internal_roi_in_same_claim():
    question = (
        "Giải thích điều gì xảy ra khi volume "
        "giảm rồi phục hồi."
    )

    assert split_claim_segments(
        question
    ) == [
        question,
    ]


def test_split_claim_segments_splits_roi_before_known_claim_starter():
    assert split_claim_segments(
        (
            "So sánh volume theo thời gian "
            "rồi cho mình biết volume mới nhất."
        )
    ) == [
        "So sánh volume theo thời gian",
        "cho mình biết volume mới nhất.",
    ]


def test_split_claim_segments_splits_period_before_known_claim_starter():
    assert split_claim_segments(
        (
            "Compare volume over time. "
            "Tell me the latest volume."
        )
    ) == [
        "Compare volume over time",
        "Tell me the latest volume.",
    ]


def test_split_claim_segments_keeps_period_without_known_starter():
    question = (
        "Explain whether volume is healthy. "
        "Use the current threshold."
    )

    assert split_claim_segments(
        question
    ) == [
        question,
    ]