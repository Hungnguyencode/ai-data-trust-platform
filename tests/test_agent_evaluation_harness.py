from types import SimpleNamespace

from src.assistant import controlled_tools
from src.assistant.llm_provider import (
    LLMProviderConfig,
)
from src.assistant.platform_copilot import (
    answer_copilot_question,
)


def _diagnosis() -> dict:
    return {
        "catalog_id": 1,
        "latest_version_id": 7,
        "overall_state": "ACTION_REQUIRED",
        "findings": [
            {
                "code": "FRESHNESS_STALE",
                "category": "freshness",
                "severity": "HIGH",
                "message": (
                    "Dataset freshness is stale."
                ),
                "evidence": {
                    "freshness_status": "STALE",
                },
            },
        ],
        "recommended_actions": [
            {
                "code": "REFRESH_DATASET",
                "priority": 1,
                "action": "Refresh the dataset.",
                "reason": (
                    "The latest freshness "
                    "check is stale."
                ),
            },
        ],
        "summary": {
            "finding_count": 1,
            "high_count": 1,
            "warning_count": 0,
            "info_count": 0,
            "action_count": 1,
        },
    }


def _explanation() -> dict:
    return {
        "catalog_id": 1,
        "latest_version_id": 7,
        "overall_state": "ACTION_REQUIRED",
        "headline": (
            "Dataset requires action."
        ),
        "summary": (
            "Freshness evidence requires "
            "operator attention."
        ),
        "explanation": (
            "Dataset requires action because "
            "the latest freshness check is stale."
        ),
        "source_finding_codes": [
            "FRESHNESS_STALE",
        ],
        "source_action_codes": [
            "REFRESH_DATASET",
        ],
    }


def test_evaluation_not_answerable_skips_llm_provider():
    class FailIfCalledModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            raise AssertionError(
                "LLM provider must not be called "
                "for NOT_ANSWERABLE evidence."
            )

    fake_client = SimpleNamespace(
        models=FailIfCalledModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "record_id": "freshness-1",
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "record_id": "volume-1",
                },
            ],
        },
    ]

    result = answer_copilot_question(
        (
            "Compare freshness and volume "
            "history over time."
        ),
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability={
            "assessment_scope": (
                "HISTORICAL_COMPARISON"
            ),
            "assessed_evidence": [
                "freshness_history",
                "volume_history",
            ],
            "answerable_evidence": [],
            "insufficient_evidence": [
                "freshness_history",
                "volume_history",
            ],
            "unavailable_evidence": [],
            "evidence_requirements": [
                {
                    "evidence_type": (
                        "freshness_history"
                    ),
                    "minimum_item_count": 2,
                    "observed_item_count": 1,
                    "requirement_status": (
                        "INSUFFICIENT_ITEMS"
                    ),
                },
                {
                    "evidence_type": (
                        "volume_history"
                    ),
                    "minimum_item_count": 2,
                    "observed_item_count": 1,
                    "requirement_status": (
                        "INSUFFICIENT_ITEMS"
                    ),
                },
            ],
            "answerability_status": (
                "NOT_ANSWERABLE"
            ),
        },
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is False
    assert result["provider"] == "deterministic"
    assert result["model"] is None

    assert (
        result["fallback_reason"]
        == "historical_comparison_not_answerable"
    )

    assert result["error_type"] is None

    assert (
        result["answer"]
        == (
            "Platform evidence is insufficient "
            "for the requested historical "
            "comparison."
        )
    )

    assert result["source_finding_codes"] == [
        "FRESHNESS_STALE",
    ]

    assert result["source_action_codes"] == [
        "REFRESH_DATASET",
    ]


def test_evaluation_partial_scopes_restricted_evidence_before_llm():
    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert (
                "freshness-allowed-marker"
                in contents
            )

            assert (
                "volume-restricted-marker"
                not in contents
            )

            # Restriction metadata must remain
            # even though the payload is hidden.
            assert (
                '"answerability_status": '
                '"PARTIAL"'
                in contents
            )

            assert (
                '"volume_history"'
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness comparison is "
                    "supported, while volume "
                    "comparison is limited."
                )
            )

    fake_client = SimpleNamespace(
        models=InspectPromptModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "freshness-allowed-marker"
                    ),
                },
                {
                    "marker": (
                        "freshness-allowed-marker-2"
                    ),
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "volume-restricted-marker"
                    ),
                },
            ],
        },
    ]

    result = answer_copilot_question(
        (
            "Compare freshness and volume "
            "history over time."
        ),
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability={
            "assessment_scope": (
                "HISTORICAL_COMPARISON"
            ),
            "assessed_evidence": [
                "freshness_history",
                "volume_history",
            ],
            "answerable_evidence": [
                "freshness_history",
            ],
            "insufficient_evidence": [
                "volume_history",
            ],
            "unavailable_evidence": [],
            "evidence_requirements": [
                {
                    "evidence_type": (
                        "freshness_history"
                    ),
                    "minimum_item_count": 2,
                    "observed_item_count": 2,
                    "requirement_status": (
                        "SATISFIED"
                    ),
                },
                {
                    "evidence_type": (
                        "volume_history"
                    ),
                    "minimum_item_count": 2,
                    "observed_item_count": 1,
                    "requirement_status": (
                        "INSUFFICIENT_ITEMS"
                    ),
                },
            ],
            "answerability_status": (
                "PARTIAL"
            ),
        },
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is True

    assert result["provider"] == "gemini"

    assert (
        result["answer"]
        == (
            "Freshness comparison is "
            "supported, while volume "
            "comparison is limited."
        )
    )

    assert result["fallback_reason"] is None
    assert result["error_type"] is None


def test_evaluation_empty_retrieval_is_not_available_evidence(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        assert name in {
            "get_freshness_history",
            "get_volume_history",
        }

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_sufficiency: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness and "
                "volume history."
            ),
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert agent_evidence_sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "available_evidence": [],
        "empty_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "unavailable_evidence": [],
        "evidence_details": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "availability_status": "EMPTY",
                "item_count": 0,
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "availability_status": "EMPTY",
                "item_count": 0,
            },
        ],
        "sufficiency_status": "INSUFFICIENT",
    }


def test_evaluation_failed_retrieval_is_unavailable_not_empty(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            raise RuntimeError(
                "simulated freshness failure"
            )

        assert name == "get_volume_history"

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "row_count": 100,
                },
            ],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_sufficiency: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness and "
                "volume history."
            ),
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_volume_history",
    ]

    assert agent_evidence_sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "available_evidence": [
            "volume_history",
        ],
        "empty_evidence": [],
        "unavailable_evidence": [
            "freshness_history",
        ],
        "evidence_details": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "availability_status": (
                    "UNAVAILABLE"
                ),
                "item_count": None,
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "availability_status": (
                    "AVAILABLE"
                ),
                "item_count": 1,
            },
        ],
        "sufficiency_status": "PARTIAL",
    }


def test_evaluation_cross_layer_partial_answerability_scopes_llm_context(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "marker": (
                            "freshness-history-1"
                        ),
                    },
                    {
                        "marker": (
                            "freshness-history-2"
                        ),
                    },
                ],
            }

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "marker": (
                            "volume-history-restricted"
                        ),
                    },
                ],
            }

        raise AssertionError(
            f"Unexpected controlled tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    evidence_sufficiency: dict = {}
    evidence_answerability: dict = {}

    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                evidence_sufficiency
            ),
            agent_evidence_answerability=(
                evidence_answerability
            ),
        )
    )

    assert (
        evidence_sufficiency[
            "sufficiency_status"
        ]
        == "SUFFICIENT"
    )

    assert (
        evidence_sufficiency[
            "available_evidence"
        ]
        == [
            "freshness_history",
            "volume_history",
        ]
    )

    assert (
        evidence_answerability[
            "assessment_scope"
        ]
        == "HISTORICAL_COMPARISON"
    )

    assert (
        evidence_answerability[
            "answerability_status"
        ]
        == "PARTIAL"
    )

    assert (
        evidence_answerability[
            "answerable_evidence"
        ]
        == [
            "freshness_history",
        ]
    )

    assert (
        evidence_answerability[
            "insufficient_evidence"
        ]
        == [
            "volume_history",
        ]
    )

    assert (
        evidence_answerability[
            "unavailable_evidence"
        ]
        == []
    )

    assert (
        evidence_answerability[
            "evidence_requirements"
        ]
        == [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 2,
                "requirement_status": (
                    "SATISFIED"
                ),
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 1,
                "requirement_status": (
                    "INSUFFICIENT_ITEMS"
                ),
            },
        ]
    )

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert (
                "freshness-history-1"
                in contents
            )

            assert (
                "freshness-history-2"
                in contents
            )

            assert (
                "volume-history-restricted"
                not in contents
            )

            assert (
                '"answerability_status": '
                '"PARTIAL"'
                in contents
            )

            assert (
                '"volume_history"'
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness comparison is "
                    "supported; volume comparison "
                    "is not sufficiently supported."
                )
            )

    fake_client = SimpleNamespace(
        models=InspectPromptModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = answer_copilot_question(
        question,
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability=(
            evidence_answerability
        ),
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is True
    assert result["provider"] == "gemini"
    assert result["fallback_reason"] is None
    assert result["error_type"] is None


def test_evaluation_cross_layer_not_answerable_skips_llm_provider(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "marker": (
                            "freshness-single-record"
                        ),
                    },
                ],
            }

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [],
            }

        raise AssertionError(
            f"Unexpected controlled tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    evidence_sufficiency: dict = {}
    evidence_answerability: dict = {}

    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                evidence_sufficiency
            ),
            agent_evidence_answerability=(
                evidence_answerability
            ),
        )
    )

    assert (
        evidence_sufficiency[
            "sufficiency_status"
        ]
        == "PARTIAL"
    )

    assert (
        evidence_sufficiency[
            "available_evidence"
        ]
        == [
            "freshness_history",
        ]
    )

    assert (
        evidence_sufficiency[
            "empty_evidence"
        ]
        == [
            "volume_history",
        ]
    )

    assert (
        evidence_sufficiency[
            "unavailable_evidence"
        ]
        == []
    )

    assert (
        evidence_answerability[
            "assessment_scope"
        ]
        == "HISTORICAL_COMPARISON"
    )

    assert (
        evidence_answerability[
            "answerability_status"
        ]
        == "NOT_ANSWERABLE"
    )

    assert (
        evidence_answerability[
            "answerable_evidence"
        ]
        == []
    )

    assert (
        evidence_answerability[
            "insufficient_evidence"
        ]
        == [
            "freshness_history",
            "volume_history",
        ]
    )

    assert (
        evidence_answerability[
            "unavailable_evidence"
        ]
        == []
    )

    assert (
        evidence_answerability[
            "evidence_requirements"
        ]
        == [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 1,
                "requirement_status": (
                    "INSUFFICIENT_ITEMS"
                ),
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 0,
                "requirement_status": (
                    "INSUFFICIENT_ITEMS"
                ),
            },
        ]
    )

    class FailIfCalledModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            raise AssertionError(
                "LLM provider must not be called "
                "after deterministic "
                "NOT_ANSWERABLE assessment."
            )

    fake_client = SimpleNamespace(
        models=FailIfCalledModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = answer_copilot_question(
        question,
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability=(
            evidence_answerability
        ),
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is False
    assert result["provider"] == "deterministic"
    assert result["model"] is None

    assert (
        result["fallback_reason"]
        == "historical_comparison_not_answerable"
    )

    assert result["error_type"] is None


def test_evaluation_non_comparison_history_is_not_subject_to_comparison_gate(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        assert name == "get_freshness_history"

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "single-freshness-history-record"
                    ),
                },
            ],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    evidence_sufficiency: dict = {}
    evidence_answerability: dict = {}

    question = "Show freshness history."

    controlled_tool_results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                evidence_sufficiency
            ),
            agent_evidence_answerability=(
                evidence_answerability
            ),
        )
    )

    assert (
        evidence_sufficiency[
            "sufficiency_status"
        ]
        == "SUFFICIENT"
    )

    assert (
        evidence_sufficiency[
            "available_evidence"
        ]
        == [
            "freshness_history",
        ]
    )

    assert (
        evidence_answerability[
            "assessment_scope"
        ]
        == "NOT_APPLICABLE"
    )

    assert (
        evidence_answerability[
            "answerability_status"
        ]
        == "NOT_APPLICABLE"
    )

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert (
                "single-freshness-history-record"
                in contents
            )

            assert (
                '"answerability_status": '
                '"NOT_APPLICABLE"'
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness history is available."
                )
            )

    fake_client = SimpleNamespace(
        models=InspectPromptModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = answer_copilot_question(
        question,
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability=(
            evidence_answerability
        ),
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is True
    assert result["provider"] == "gemini"
    assert result["fallback_reason"] is None
    assert result["error_type"] is None


def test_evaluation_mutation_request_does_not_execute_controlled_tools(
    monkeypatch,
):
    question = (
        "Promote this dataset and show "
        "freshness, pipeline, and alerts."
    )

    plan = (
        controlled_tools
        .plan_controlled_tool_requests(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
        )
    )

    assert plan == []

    def fail_execute_tool(
        name,
        arguments,
    ):
        del name
        del arguments

        raise AssertionError(
            "Mutation request must not execute "
            "controlled evidence tools."
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fail_execute_tool,
    )

    agent_run_summary: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_run_summary=(
                agent_run_summary
            ),
        )
    )

    assert results == []

    assert agent_run_summary == {
        "round_count": 0,
        "stop_reason": "NO_TOOL_REQUESTS",
        "attempted_tool_count": 0,
        "accepted_evidence_count": 0,
        "failed_tool_count": 0,
    }


def test_evaluation_cross_layer_answerable_preserves_all_evidence(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "marker": "freshness-1",
                    },
                    {
                        "marker": "freshness-2",
                    },
                ],
            }

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "marker": "volume-1",
                    },
                    {
                        "marker": "volume-2",
                    },
                ],
            }

        raise AssertionError(
            f"Unexpected controlled tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    evidence_sufficiency: dict = {}
    evidence_answerability: dict = {}

    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            agent_evidence_sufficiency=(
                evidence_sufficiency
            ),
            agent_evidence_answerability=(
                evidence_answerability
            ),
        )
    )

    assert (
        evidence_sufficiency[
            "sufficiency_status"
        ]
        == "SUFFICIENT"
    )

    assert (
        evidence_answerability[
            "answerability_status"
        ]
        == "ANSWERABLE"
    )

    assert (
        evidence_answerability[
            "answerable_evidence"
        ]
        == [
            "freshness_history",
            "volume_history",
        ]
    )

    assert (
        evidence_answerability[
            "insufficient_evidence"
        ]
        == []
    )

    assert (
        evidence_answerability[
            "unavailable_evidence"
        ]
        == []
    )

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert "freshness-1" in contents
            assert "freshness-2" in contents
            assert "volume-1" in contents
            assert "volume-2" in contents

            assert (
                '"answerability_status": '
                '"ANSWERABLE"'
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness and volume "
                    "history can be compared."
                )
            )

    fake_client = SimpleNamespace(
        models=InspectPromptModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    result = answer_copilot_question(
        question,
        _diagnosis(),
        _explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability=(
            evidence_answerability
        ),
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is True
    assert result["provider"] == "gemini"
    assert result["fallback_reason"] is None
    assert result["error_type"] is None
