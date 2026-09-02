IF OBJECT_ID('dbo.validation_history', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.validation_history (
        validation_id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,

        ingestion_event_id BIGINT NOT NULL,
        ingestion_id NVARCHAR(36) NOT NULL,

        catalog_id INT NOT NULL,
        version_id INT NOT NULL,

        policy_version NVARCHAR(50) NOT NULL,
        validation_status NVARCHAR(20) NOT NULL,
        validated_at DATETIMEOFFSET(7) NOT NULL,

        total_issues INT NOT NULL DEFAULT 0,
        high_issues INT NOT NULL DEFAULT 0,
        medium_issues INT NOT NULL DEFAULT 0,
        low_issues INT NOT NULL DEFAULT 0,

        blocking_issue_count INT NOT NULL DEFAULT 0,
        blocking_issues_json NVARCHAR(MAX) NULL,

        artifact_path NVARCHAR(2048) NOT NULL,
        validation_metadata_path NVARCHAR(2048) NOT NULL,

        rejection_reason NVARCHAR(MAX) NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_validation_history_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_validation_history_ingestion_policy
            UNIQUE (ingestion_id, policy_version),

        CONSTRAINT FK_validation_history_ingestion
            FOREIGN KEY (ingestion_event_id)
            REFERENCES dbo.ingestion_history(ingestion_event_id),

        CONSTRAINT FK_validation_history_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_validation_history_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT CK_validation_history_status
            CHECK (validation_status IN ('ACCEPTED', 'REJECTED'))
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_validation_history_catalog_validated'
      AND object_id = OBJECT_ID('dbo.validation_history')
)
BEGIN
    CREATE INDEX IX_validation_history_catalog_validated
        ON dbo.validation_history (
            catalog_id,
            validated_at DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_validation_history_version_validated'
      AND object_id = OBJECT_ID('dbo.validation_history')
)
BEGIN
    CREATE INDEX IX_validation_history_version_validated
        ON dbo.validation_history (
            version_id,
            validated_at DESC
        );
END;
GO