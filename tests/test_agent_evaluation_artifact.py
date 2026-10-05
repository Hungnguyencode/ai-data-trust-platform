from src.assistant.evaluation_artifact import (
    generate_agent_evaluation_artifact,
    main,
    serialize_agent_evaluation_report,
    write_agent_evaluation_report,
)


def test_serialize_agent_evaluation_report_is_stable_json():
    report = {
        "evaluation_version": "v1",
        "overall_status": "PASS",
        "scenario_count": 1,
        "passed_count": 1,
        "failed_count": 0,
        "scenarios": [
            {
                "scenario_id": "example",
                "description": "Example scenario.",
                "expected": {
                    "used_llm": False,
                },
                "observed": {
                    "used_llm": False,
                },
                "status": "PASS",
            },
        ],
    }

    serialized = serialize_agent_evaluation_report(
        report
    )

    assert serialized == (
        "{\n"
        '  "evaluation_version": "v1",\n'
        '  "overall_status": "PASS",\n'
        '  "scenario_count": 1,\n'
        '  "passed_count": 1,\n'
        '  "failed_count": 0,\n'
        '  "scenarios": [\n'
        "    {\n"
        '      "scenario_id": "example",\n'
        '      "description": "Example scenario.",\n'
        '      "expected": {\n'
        '        "used_llm": false\n'
        "      },\n"
        '      "observed": {\n'
        '        "used_llm": false\n'
        "      },\n"
        '      "status": "PASS"\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def test_write_agent_evaluation_report_writes_serialized_json(
    tmp_path,
):
    report = {
        "evaluation_version": "v1",
        "overall_status": "PASS",
        "scenario_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "scenarios": [],
    }

    output_path = (
        tmp_path / "agent-evaluation-report.json"
    )

    written_path = write_agent_evaluation_report(
        report,
        output_path=output_path,
    )

    assert written_path == output_path
    assert output_path.read_text(
        encoding="utf-8"
    ) == serialize_agent_evaluation_report(
        report
    )


def test_generate_agent_evaluation_artifact_runs_real_suite(
    tmp_path,
):
    output_path = (
        tmp_path / "agent-evaluation-report.json"
    )

    report = generate_agent_evaluation_artifact(
        output_path=output_path,
    )

    assert report["evaluation_version"] == "v1"
    assert report["overall_status"] == "PASS"
    assert report["scenario_count"] == 16
    assert report["passed_count"] == 16
    assert report["failed_count"] == 0

    assert output_path.read_text(
        encoding="utf-8"
    ) == serialize_agent_evaluation_report(
        report
    )


def test_main_returns_zero_for_passing_evaluation(
    tmp_path,
):
    output_path = (
        tmp_path / "agent-evaluation-report.json"
    )

    exit_code = main(
        output_path=output_path,
    )

    assert exit_code == 0
    assert output_path.exists()


def test_main_returns_one_for_failing_evaluation(
    tmp_path,
    monkeypatch,
):
    output_path = (
        tmp_path / "agent-evaluation-report.json"
    )

    failing_report = {
        "evaluation_version": "v1",
        "overall_status": "FAIL",
        "scenario_count": 1,
        "passed_count": 0,
        "failed_count": 1,
        "scenarios": [],
    }

    def fake_generate_agent_evaluation_artifact(
        *,
        output_path,
    ):
        del output_path
        return failing_report

    monkeypatch.setattr(
        "src.assistant.evaluation_artifact."
        "generate_agent_evaluation_artifact",
        fake_generate_agent_evaluation_artifact,
    )

    exit_code = main(
        output_path=output_path,
    )

    assert exit_code == 1
