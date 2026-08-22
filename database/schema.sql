CREATE DATABASE AIDataTrustPlatform;
GO

USE AIDataTrustPlatform;
GO

CREATE TABLE datasets (
    dataset_id INT IDENTITY(1,1) PRIMARY KEY,
    file_name NVARCHAR(255) NOT NULL,
    file_type NVARCHAR(50) NOT NULL,
    total_rows INT NOT NULL,
    total_columns INT NOT NULL,
    total_cells INT NOT NULL,
    missing_cells INT NOT NULL,
    duplicate_rows INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE scan_runs (
    scan_id INT IDENTITY(1,1) PRIMARY KEY,
    dataset_id INT NOT NULL,
    scan_status NVARCHAR(50) NOT NULL DEFAULT 'completed',
    total_issues INT NOT NULL DEFAULT 0,
    high_issues INT NOT NULL DEFAULT 0,
    medium_issues INT NOT NULL DEFAULT 0,
    low_issues INT NOT NULL DEFAULT 0,
    affected_columns INT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_scan_runs_datasets
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(dataset_id)
);
GO

CREATE TABLE trust_scores (
    score_id INT IDENTITY(1,1) PRIMARY KEY,
    scan_id INT NOT NULL,
    overall_score FLOAT NOT NULL,
    risk_level NVARCHAR(50) NOT NULL,
    ai_readiness NVARCHAR(255) NOT NULL,
    completeness_score FLOAT NOT NULL,
    validity_score FLOAT NOT NULL,
    uniqueness_score FLOAT NOT NULL,
    consistency_score FLOAT NOT NULL,
    anomaly_safety_score FLOAT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_trust_scores_scan_runs
        FOREIGN KEY (scan_id)
        REFERENCES scan_runs(scan_id)
);
GO

CREATE TABLE quality_issues (
    issue_id INT IDENTITY(1,1) PRIMARY KEY,
    scan_id INT NOT NULL,
    issue_type NVARCHAR(100) NOT NULL,
    column_name NVARCHAR(255) NOT NULL,
    severity NVARCHAR(50) NOT NULL,
    issue_count INT NOT NULL,
    issue_rate FLOAT NOT NULL,
    description NVARCHAR(MAX) NULL,
    recommendation NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_quality_issues_scan_runs
        FOREIGN KEY (scan_id)
        REFERENCES scan_runs(scan_id)
);
GO

CREATE TABLE privacy_findings (
    privacy_id INT IDENTITY(1,1) PRIMARY KEY,
    scan_id INT NOT NULL,
    pii_type NVARCHAR(100) NOT NULL,
    column_name NVARCHAR(255) NOT NULL,
    match_count INT NOT NULL,
    match_rate FLOAT NOT NULL,
    severity NVARCHAR(50) NOT NULL,
    detection_method NVARCHAR(255) NULL,
    masked_examples NVARCHAR(MAX) NULL,
    recommendation NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_privacy_findings_scan_runs
        FOREIGN KEY (scan_id)
        REFERENCES scan_runs(scan_id)
);
GO

CREATE TABLE anomaly_results (
    anomaly_id INT IDENTITY(1,1) PRIMARY KEY,
    scan_id INT NOT NULL,
    total_rows INT NOT NULL,
    total_anomaly_rows INT NOT NULL,
    anomaly_rate FLOAT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    risk_level NVARCHAR(50) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_anomaly_results_scan_runs
        FOREIGN KEY (scan_id)
        REFERENCES scan_runs(scan_id)
);
GO

CREATE TABLE drift_results (
    drift_id INT IDENTITY(1,1) PRIMARY KEY,
    scan_id INT NULL,
    baseline_file_name NVARCHAR(255) NULL,
    current_file_name NVARCHAR(255) NULL,
    baseline_rows INT NULL,
    current_rows INT NULL,
    baseline_columns INT NULL,
    current_columns INT NULL,
    checked_common_columns INT NULL,
    schema_drift_count INT NULL,
    drifted_columns INT NULL,
    high_drift_columns INT NULL,
    moderate_drift_columns INT NULL,
    drift_rate FLOAT NULL,
    overall_drift_level NVARCHAR(50) NULL,
    drift_score FLOAT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_drift_results_scan_runs
        FOREIGN KEY (scan_id)
        REFERENCES scan_runs(scan_id)
);
GO

