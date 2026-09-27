from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.assistant.evaluation_runner import (
    run_agent_evaluation_suite,
)


def serialize_agent_evaluation_report(
    report: Mapping[str, Any],
) -> str:
    return (
        json.dumps(
            dict(report),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def write_agent_evaluation_report(
    report: Mapping[str, Any],
    *,
    output_path: Path,
) -> Path:
    output_path.write_text(
        serialize_agent_evaluation_report(
            report
        ),
        encoding="utf-8",
    )

    return output_path


def generate_agent_evaluation_artifact(
    *,
    output_path: Path,
) -> dict[str, Any]:
    report = run_agent_evaluation_suite()

    write_agent_evaluation_report(
        report,
        output_path=output_path,
    )

    return report


def main(
    *,
    output_path: Path = Path(
        "agent-evaluation-report.json"
    ),
) -> int:
    report = generate_agent_evaluation_artifact(
        output_path=output_path,
    )

    if report["overall_status"] == "PASS":
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )