IF OBJECT_ID(
    'dbo.dataset_freshness_policies',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.dataset_freshness_policies (
        freshness_policy_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,

        max_age_minutes INT NOT NULL,

        is_enabled BIT NOT NULL
            CONSTRAINT DF_dataset_freshness_policies_enabled
            DEFAULT 1,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_freshness_policies_created_at
            DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_freshness_policies_updated_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_dataset_freshness_policies_catalog
            UNIQUE (
                catalog_id
            ),

        CONSTRAINT FK_dataset_freshness_policies_catalog
            FOREIGN KEY (
                catalog_id
            )
            REFERENCES dbo.dataset_catalog(
                catalog_id
            ),

        CONSTRAINT CK_dataset_freshness_policies_max_age
            CHECK (
                max_age_minutes > 0
            )
    );
END;
GO


IF OBJECT_ID(
    'dbo.dataset_freshness_history',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.dataset_freshness_history (
        freshness_check_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,

        ingestion_event_id BIGINT NULL,
        version_id INT NULL,

        max_age_minutes INT NOT NULL,
        age_minutes INT NULL,

        freshness_status NVARCHAR(20) NOT NULL,

        latest_ingested_at DATETIMEOFFSET(7) NULL,

        checked_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_freshness_history_checked_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_dataset_freshness_history_catalog
            FOREIGN KEY (
                catalog_id
            )
            REFERENCES dbo.dataset_catalog(
                catalog_id
            ),

        CONSTRAINT FK_dataset_freshness_history_ingestion
            FOREIGN KEY (
                ingestion_event_id
            )
            REFERENCES dbo.ingestion_history(
                ingestion_event_id
            ),

        CONSTRAINT FK_dataset_freshness_history_version
            FOREIGN KEY (
                version_id
            )
            REFERENCES dbo.dataset_versions(
                version_id
            ),

        CONSTRAINT CK_dataset_freshness_history_status
            CHECK (
                freshness_status IN (
                    'FRESH',
                    'STALE',
                    'NO_DATA'
                )
            ),

        CONSTRAINT CK_dataset_freshness_history_max_age
            CHECK (
                max_age_minutes > 0
            ),

        CONSTRAINT CK_dataset_freshness_history_age
            CHECK (
                age_minutes IS NULL
                OR age_minutes >= 0
            )
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name =
        'IX_dataset_freshness_history_catalog_checked'
      AND object_id = OBJECT_ID(
          'dbo.dataset_freshness_history'
      )
)
BEGIN
    CREATE INDEX
        IX_dataset_freshness_history_catalog_checked
    ON dbo.dataset_freshness_history (
        catalog_id,
        checked_at DESC,
        freshness_check_id DESC
    );
END;
GO