from __future__ import annotations

PAGE_GROUPS: dict[str, tuple[str, ...]] = {
    "DATA": (
        "app/views/1_upload_dataset.py",
        "app/views/2_data_profile.py",
    ),
    "TRUST": (
        "app/views/3_quality_issues.py",
        "app/views/4_trust_score.py",
        "app/views/5_anomaly_detection.py",
        "app/views/6_drift_analysis.py",
        "app/views/7_privacy_risk.py",
    ),
    "INTELLIGENCE": (
        "app/views/8_ai_assistant.py",
        "app/views/9_reports.py",
    ),
    "GOVERNANCE": (
        "app/views/11_data_contracts.py",
    ),
    "OPERATIONS": (
        "app/views/10_pipeline_operations.py",
        "app/views/12_dataset_freshness.py",
        "app/views/13_dataset_volume.py",
        "app/views/14_observability_overview.py",
    ),
}


HOME_PAGE = "app/dashboard.py"

PAGE_METADATA = {
    "app/views/1_upload_dataset.py": ("Upload Dataset", ":material/upload_file:"),
    "app/views/2_data_profile.py": ("Data Profile", ":material/analytics:"),
    "app/views/3_quality_issues.py": ("Quality Issues", ":material/warning:"),
    "app/views/4_trust_score.py": ("Trust Score", ":material/verified_user:"),
    "app/views/5_anomaly_detection.py": ("Anomaly Detection", ":material/monitor_heart:"),
    "app/views/6_drift_analysis.py": ("Drift Analysis", ":material/bar_chart:"),
    "app/views/7_privacy_risk.py": ("Privacy Risk", ":material/privacy_tip:"),
    "app/views/8_ai_assistant.py": ("Data Trust Copilot", ":material/auto_awesome:"),
    "app/views/9_reports.py": ("Reports", ":material/description:"),
    "app/views/10_pipeline_operations.py": ("Pipeline Operations", ":material/settings:"),
    "app/views/11_data_contracts.py": ("Data Contracts", ":material/fact_check:"),
    "app/views/12_dataset_freshness.py": ("Dataset Freshness", ":material/update:"),
    "app/views/13_dataset_volume.py": ("Dataset Volume", ":material/database:"),
    "app/views/14_observability_overview.py": ("Observability Overview", ":material/monitoring:"),
}
