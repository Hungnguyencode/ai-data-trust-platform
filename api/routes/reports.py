from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.report_schema import (
    HtmlReportRequest,
    HtmlReportResponse,
    HtmlReportSaveRequest,
    HtmlReportSaveResponse,
)
from src.reports.html_report import (
    build_data_quality_html_report,
    generate_report_filename,
    save_html_report,
)
from src.utils.config import REPORTS_DIR

router = APIRouter()


@router.post(
    "/html",
    response_model=HtmlReportResponse,
)
def generate_html_report(
    payload: HtmlReportRequest,
) -> HtmlReportResponse:
    quality_report = None

    if payload.quality is not None:
        quality_report = {
            "summary": dict(
                payload.quality.summary
            ),
            "issues_df": pd.DataFrame(
                payload.quality.issue_records
            ),
        }

    trust_score_report = None

    if payload.trust_score is not None:
        trust_score_report = {
            "overall_score": (
                payload.trust_score.overall_score
            ),
            "risk_level": (
                payload.trust_score.risk_level
            ),
            "ai_readiness": (
                payload.trust_score.ai_readiness
            ),
            "conclusion": (
                payload.trust_score.conclusion
            ),
            "breakdown_df": pd.DataFrame(
                payload.trust_score.breakdown_records
            ),
        }

    privacy_report = None

    if payload.privacy is not None:
        privacy_report = {
            "summary": dict(
                payload.privacy.summary
            ),
            "findings_df": pd.DataFrame(
                payload.privacy.finding_records
            ),
        }

    drift_report = None

    if payload.drift is not None:
        drift_report = {
            "summary": dict(
                payload.drift.summary
            ),
            "baseline_file_name": (
                payload.drift.baseline_file_name
            ),
            "current_file_name": (
                payload.drift.current_file_name
            ),
            "numeric_drift_df": pd.DataFrame(
                payload.drift.numeric_drift_records
            ),
            "categorical_drift_df": pd.DataFrame(
                payload.drift.categorical_drift_records
            ),
            "schema_report": {
                "changes_df": pd.DataFrame(
                    payload.drift.schema_change_records
                ),
            },
        }

    profile = None

    if payload.profile is not None:
        profile = {
            "basic_info": dict(
                payload.profile.basic_info
            ),
        }

    html_content = build_data_quality_html_report(
        file_name=payload.file_name,
        file_type=payload.file_type,
        df=pd.DataFrame(),
        profile=profile,
        quality_report=quality_report,
        trust_score_report=trust_score_report,
        privacy_report=privacy_report,
        drift_report=drift_report,
        total_rows=payload.total_rows,
        total_columns=payload.total_columns,
    )

    return HtmlReportResponse(
        report_file_name=generate_report_filename(),
        html_content=html_content,
    )


@router.post(
    "/html/save",
    response_model=HtmlReportSaveResponse,
)
def save_generated_html_report(
    payload: HtmlReportSaveRequest,
) -> HtmlReportSaveResponse:
    report_file_name = (
        payload.report_file_name
    )

    is_safe_file_name = (
        bool(report_file_name)
        and PurePosixPath(
            report_file_name
        ).name
        == report_file_name
        and PureWindowsPath(
            report_file_name
        ).name
        == report_file_name
        and report_file_name
        not in {".", ".."}
    )

    if not is_safe_file_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid report file name.",
        )
    output_path = save_html_report(
        html_content=payload.html_content,
        output_dir=REPORTS_DIR,
        file_name=report_file_name,
    )

    return HtmlReportSaveResponse(
        report_file_name=report_file_name,
        saved_path=str(output_path),
    )