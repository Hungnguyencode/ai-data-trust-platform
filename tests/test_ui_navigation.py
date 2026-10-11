from pathlib import Path


def test_navigation_registry_covers_all_existing_pages():
    from app.ui.navigation import PAGE_GROUPS

    assert list(PAGE_GROUPS) == [
        "DATA",
        "TRUST",
        "INTELLIGENCE",
        "GOVERNANCE",
        "OPERATIONS",
    ]

    assert PAGE_GROUPS["DATA"] == (
        "app/views/1_upload_dataset.py",
        "app/views/2_data_profile.py",
    )

    assert PAGE_GROUPS["TRUST"] == (
        "app/views/3_quality_issues.py",
        "app/views/4_trust_score.py",
        "app/views/5_anomaly_detection.py",
        "app/views/6_drift_analysis.py",
        "app/views/7_privacy_risk.py",
    )

    assert PAGE_GROUPS["INTELLIGENCE"] == (
        "app/views/8_ai_assistant.py",
        "app/views/9_reports.py",
    )

    assert PAGE_GROUPS["GOVERNANCE"] == (
        "app/views/11_data_contracts.py",
    )

    assert PAGE_GROUPS["OPERATIONS"] == (
        "app/views/10_pipeline_operations.py",
        "app/views/12_dataset_freshness.py",
        "app/views/13_dataset_volume.py",
        "app/views/14_observability_overview.py",
    )

    registered = [
        page
        for pages in PAGE_GROUPS.values()
        for page in pages
    ]

    project_root = Path(__file__).resolve().parents[1]

    existing = {
        path.relative_to(project_root).as_posix()
        for path in (project_root / "app" / "views").glob("*.py")
    }

    assert len(registered) == len(set(registered)) == 14
    assert set(registered) == existing



def test_navigation_registry_defines_separate_home_page():
    from app.ui.navigation import HOME_PAGE, PAGE_GROUPS

    assert HOME_PAGE == "app/dashboard.py"
    assert HOME_PAGE != "app/streamlit_app.py"

    registered_pages = {
        page
        for pages in PAGE_GROUPS.values()
        for page in pages
    }

    assert HOME_PAGE not in registered_pages


def test_navigation_registry_preserves_page_metadata():
    from app.ui.navigation import PAGE_GROUPS, PAGE_METADATA

    expected = {
        "app/views/1_upload_dataset.py": (
            "Upload Dataset", ":material/upload_file:"
        ),
        "app/views/2_data_profile.py": (
            "Data Profile", ":material/analytics:"
        ),
        "app/views/3_quality_issues.py": (
            "Quality Issues", ":material/warning:"
        ),
        "app/views/4_trust_score.py": (
            "Trust Score", ":material/verified_user:"
        ),
        "app/views/5_anomaly_detection.py": (
            "Anomaly Detection", ":material/monitor_heart:"
        ),
        "app/views/6_drift_analysis.py": (
            "Drift Analysis", ":material/bar_chart:"
        ),
        "app/views/7_privacy_risk.py": (
            "Privacy Risk", ":material/privacy_tip:"
        ),
        "app/views/8_ai_assistant.py": (
            "Data Trust Copilot", ":material/auto_awesome:"
        ),
        "app/views/9_reports.py": (
            "Reports", ":material/description:"
        ),
        "app/views/10_pipeline_operations.py": (
            "Pipeline Operations", ":material/settings:"
        ),
        "app/views/11_data_contracts.py": (
            "Data Contracts", ":material/fact_check:"
        ),
        "app/views/12_dataset_freshness.py": (
            "Dataset Freshness", ":material/update:"
        ),
        "app/views/13_dataset_volume.py": (
            "Dataset Volume", ":material/database:"
        ),
        "app/views/14_observability_overview.py": (
            "Observability Overview", ":material/monitoring:"
        ),
    }

    registered = {
        path
        for paths in PAGE_GROUPS.values()
        for path in paths
    }

    assert PAGE_METADATA == expected
    assert set(PAGE_METADATA) == registered


def test_enterprise_navigation_icons_match_sample():
    from app.ui.navigation import PAGE_METADATA

    expected_icons = {
        "app/views/4_trust_score.py": ":material/verified_user:",
        "app/views/5_anomaly_detection.py": ":material/monitor_heart:",
        "app/views/6_drift_analysis.py": ":material/bar_chart:",
        "app/views/10_pipeline_operations.py": ":material/settings:",
    }

    for path, expected_icon in expected_icons.items():
        assert PAGE_METADATA[path][1] == expected_icon, path
