from __future__ import annotations

import ast
from pathlib import Path

PIPELINE_OPERATIONS_PAGE = Path(
    "app/pages/10_pipeline_operations.py"
)

DATA_CONTRACTS_PAGE = Path(
    "app/pages/11_data_contracts.py"
)

AI_ASSISTANT_PAGE = Path(
    "app/pages/8_ai_assistant.py"
)

QUALITY_ISSUES_PAGE = Path(
    "app/pages/3_quality_issues.py"
)

TRUST_SCORE_PAGE = Path(
    "app/pages/4_trust_score.py"
)

REPORTS_PAGE = Path(
    "app/pages/9_reports.py"
)

DRIFT_ANALYSIS_PAGE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "pages"
    / "6_drift_analysis.py"
)

UPLOAD_DATASET_PAGE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "pages"
    / "1_upload_dataset.py"
)

ANOMALY_DETECTION_PAGE = Path(
    "app/pages/5_anomaly_detection.py"
)

PRIVACY_RISK_PAGE = Path(
    "app/pages/7_privacy_risk.py"
)


def test_pipeline_operations_page_uses_service_boundary():
    source = PIPELINE_OPERATIONS_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    function_names = {
        node.name
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
    }

    referenced_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }

    assert "requests" not in imported_modules
    assert "requests" not in referenced_names

    assert (
        "app.services.pipeline_operations_api"
        in imported_from_modules
    )

    assert {
        "load_pipeline_runs",
        "load_pipeline_run",
        "load_operational_events",
    }.isdisjoint(
        function_names
    )


def test_data_contracts_page_uses_service_boundary():
    source = DATA_CONTRACTS_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    function_names = {
        node.name
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
    }

    referenced_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }

    assert "requests" not in imported_modules
    assert "requests" not in referenced_names

    assert (
        "app.services.data_contracts_api"
        in imported_from_modules
    )

    assert {
        "load_contract_history",
        "load_active_contract",
        "activate_contract",
        "create_contract",
    }.isdisjoint(
        function_names
    )


def test_ai_assistant_page_uses_service_boundary():
    source = AI_ASSISTANT_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    referenced_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    assert "requests" not in imported_modules
    assert "requests" not in referenced_names

    assert (
        "app.services.assistant_api"
        in imported_from_modules
    )

    assert "check_api_health" in {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.services.assistant_api"
        for alias in node.names
    }


def test_quality_issues_page_uses_service_boundary():
    source = QUALITY_ISSUES_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.dataset_quality_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    assert (
        "src.validation.rule_engine"
        not in imported_from_modules
    )

    assert (
        "app.services.dataset_quality_api"
        in imported_from_modules
    )

    assert (
        "load_dataset_quality"
        in imported_service_names
    )

    assert (
        "DatasetQualityApiError"
        in imported_service_names
    )

    assert (
        "DatasetQualityApiError"
        in caught_exception_names
    )


def test_trust_score_page_uses_service_boundary():
    source = TRUST_SCORE_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.trust_score_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    imported_scan_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.scan_api"
        for alias in node.names
    }

    assert (
        "src.scoring.score_engine"
        not in imported_from_modules
    )

    assert (
        "src.validation.rule_engine"
        not in imported_from_modules
    )

    assert (
        "app.services.trust_score_api"
        in imported_from_modules
    )

    assert (
        "load_trust_score"
        in imported_service_names
    )

    assert (
        "TrustScoreApiError"
        in imported_service_names
    )

    assert (
        "TrustScoreApiError"
        in caught_exception_names
    )

    assert (
        "database.repositories.scan_repository"
        not in imported_from_modules
    )

    assert (
        "app.services.scan_api"
        in imported_from_modules
    )

    assert (
        "save_full_scan"
        in imported_scan_service_names
    )

    assert (
        "ScanApiError"
        in imported_scan_service_names
    )

    assert (
        "ScanApiError"
        in caught_exception_names
    )


def test_reports_page_uses_scan_service_boundary():
    source = REPORTS_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_scan_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.scan_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    imported_platform_status_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.platform_status_api"
        for alias in node.names
    }

    imported_report_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.report_api"
        for alias in node.names
    }

    imported_html_report_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "src.reports.html_report"
        for alias in node.names
    }

    assert (
        "database.repositories.scan_repository"
        not in imported_from_modules
    )

    assert (
        "app.services.scan_api"
        in imported_from_modules
    )

    assert (
        "load_scan_history"
        in imported_scan_service_names
    )

    assert (
        "load_scan_detail"
        in imported_scan_service_names
    )

    assert (
        "ScanApiError"
        in imported_scan_service_names
    )

    assert (
        "ScanApiError"
        in caught_exception_names
    )

    assert (
        "database.db"
        not in imported_from_modules
    )

    assert (
        "app.services.platform_status_api"
        in imported_from_modules
    )

    assert (
        "check_database_connection"
        in imported_platform_status_names
    )

    assert (
        "build_data_quality_html_report"
        not in imported_html_report_names
    )

    assert (
        "generate_report_filename"
        not in imported_html_report_names
    )

    assert (
        "app.services.report_api"
        in imported_from_modules
    )

    assert (
        "generate_html_report"
        in imported_report_service_names
    )

    assert (
        "ReportApiError"
        in imported_report_service_names
    )

    assert (
        "ReportApiError"
        in caught_exception_names
    )

    assert (
        "src.reports.html_report"
        not in imported_from_modules
    )

    assert (
        "src.utils.config"
        not in imported_from_modules
    )

    assert (
        "save_html_report"
        in imported_report_service_names
    )


def test_drift_page_uses_dataset_parse_service_boundary():
    source = DRIFT_ANALYSIS_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_parse_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.dataset_parse_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    assert (
        "src.ingestion.file_loader"
        not in imported_from_modules
    )

    assert (
        "app.services.dataset_parse_api"
        in imported_from_modules
    )

    assert (
        "parse_dataset"
        in imported_parse_service_names
    )

    assert (
        "DatasetParseApiError"
        in imported_parse_service_names
    )

    assert (
        "DatasetParseApiError"
        in caught_exception_names
    )

    assert (
        "from src.drift.data_drift import"
        not in source
    )

    assert (
        "from app.services.drift_api import ("
        in source
    )

    assert "DriftApiError," in source
    assert "analyze_drift," in source
    assert (
        "get_categorical_distribution,"
        in source
    )


def test_upload_dataset_page_uses_platform_status_service_boundary():
    source = UPLOAD_DATASET_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_status_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.platform_status_api"
        for alias in node.names
    }

    imported_lineage_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.dataset_lineage_api"
        for alias in node.names
    }

    imported_workflow_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.dataset_workflow_api"
        for alias in node.names
    }

    assert (
        "database.repositories.lineage_repository"
        not in imported_from_modules
    )

    assert (
        "get_version_lineage"
        not in source
    )

    assert (
        "get_catalog_lineage"
        not in source
    )

    assert (
        "load_catalog_lineage"
        in imported_lineage_service_names
    )

    assert (
        "app.services.dataset_lineage_api"
        in imported_from_modules
    )

    assert (
        "load_dataset_lineage"
        in imported_lineage_service_names
    )

    assert (
        "get_dataset_version_history"
        not in source
    )

    assert (
        "load_dataset_version_history"
        in imported_lineage_service_names
    )

    assert "database.db" not in imported_from_modules

    assert (
        "app.services.platform_status_api"
        in imported_from_modules
    )

    assert (
        "check_database_connection"
        in imported_status_service_names
    )

    assert (
        "get_ingestion_history"
        not in source
    )

    assert (
        "load_ingestion_history"
        in imported_lineage_service_names
    )

    assert (
        "get_validation_history"
        not in source
    )

    assert (
        "load_validation_history"
        in imported_lineage_service_names
    )

    assert (
        "get_governance_history"
        not in source
    )

    assert (
        "load_governance_history"
        in imported_lineage_service_names
    )

    assert (
        "get_catalog_lifecycle"
        not in source
    )

    assert (
        "load_catalog_lifecycle"
        in imported_lineage_service_names
    )

    assert (
        "get_lifecycle_history"
        not in source
    )

    assert (
        "load_lifecycle_history"
        in imported_lineage_service_names
    )

    assert (
        "database.repositories.version_repository"
        not in imported_from_modules
    )

    assert (
        "promote_dataset_version"
        in imported_lineage_service_names
    )

    assert (
        "src.lifecycle.dataset_lifecycle"
        not in imported_from_modules
    )

    assert (
        "is_governed_promotion_eligible"
        not in source
    )

    assert (
        "src.ingestion.contracts"
        not in imported_from_modules
    )

    assert (
        "src.ingestion.ingestion_service"
        not in imported_from_modules
    )

    assert (
        "src.workflows"
        not in imported_from_modules
    )

    assert (
        "app.services.dataset_workflow_api"
        in imported_from_modules
    )

    assert {
        "DatasetWorkflowApiError",
        "continue_dataset_workflow",
        "ingest_dataset",
    }.issubset(
        imported_workflow_service_names
    )


def test_anomaly_detection_page_uses_service_boundary():
    source = ANOMALY_DETECTION_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.anomaly_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    assert (
        "src.anomaly.anomaly_engine"
        not in imported_from_modules
    )

    assert (
        "app.services.anomaly_api"
        in imported_from_modules
    )

    assert (
        "run_anomaly_detection"
        in imported_service_names
    )

    assert (
        "AnomalyApiError"
        in imported_service_names
    )

    assert (
        "AnomalyApiError"
        in caught_exception_names
    )


def test_privacy_risk_page_uses_service_boundary():
    source = PRIVACY_RISK_PAGE.read_text(
        encoding="utf-8",
    )
    tree = ast.parse(source)

    imported_from_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
    }

    imported_service_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.privacy_api"
        for alias in node.names
    }

    caught_exception_names = {
        node.type.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
    }

    assert (
        "src.privacy.pii_detector"
        not in imported_from_modules
    )

    assert (
        "app.services.privacy_api"
        in imported_from_modules
    )

    assert (
        "run_privacy_scan"
        in imported_service_names
    )

    assert (
        "PrivacyApiError"
        in imported_service_names
    )

    assert (
        "PrivacyApiError"
        in caught_exception_names
    )