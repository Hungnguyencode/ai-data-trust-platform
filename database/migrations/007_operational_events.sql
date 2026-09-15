IF OBJECT_ID(
    'dbo.operational_events',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.operational_events (
        operational_event_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        event_key NVARCHAR(255) NOT NULL,
        event_type NVARCHAR(80) NOT NULL,
        severity NVARCHAR(20) NOT NULL,
        event_source NVARCHAR(50) NOT NULL,
        event_stage NVARCHAR(80) NULL,

        catalog_id INT NULL,
        version_id INT NULL,
        pipeline_run_id BIGINT NULL,
        reference_id BIGINT NULL,

        message NVARCHAR(1000) NOT NULL,
        detail_json NVARCHAR(MAX) NULL,

        occurred_at DATETIME2 NOT NULL
            CONSTRAINT DF_operational_events_occurred_at
            DEFAULT SYSUTCDATETIME(),

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_operational_events_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_operational_events_key
            UNIQUE (
                event_key
            ),

        CONSTRAINT FK_operational_events_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_operational_events_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT FK_operational_events_pipeline_run
            FOREIGN KEY (pipeline_run_id)
            REFERENCES dbo.pipeline_runs(pipeline_run_id),

        CONSTRAINT CK_operational_events_severity
            CHECK (
                severity IN (
                    'INFO',
                    'WARNING',
                    'ERROR',
                    'CRITICAL'
                )
            ),

        CONSTRAINT CK_operational_events_type
            CHECK (
                LEN(
                    LTRIM(
                        RTRIM(event_type)
                    )
                ) > 0
            ),

        CONSTRAINT CK_operational_events_source
            CHECK (
                LEN(
                    LTRIM(
                        RTRIM(event_source)
                    )
                ) > 0
            ),

        CONSTRAINT CK_operational_events_message
            CHECK (
                LEN(
                    LTRIM(
                        RTRIM(message)
                    )
                ) > 0
            ),

        CONSTRAINT CK_operational_events_detail_json
            CHECK (
                detail_json IS NULL
                OR ISJSON(detail_json) = 1
            )
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_operational_events_occurred'
      AND object_id = OBJECT_ID(
          'dbo.operational_events'
      )
)
BEGIN
    CREATE INDEX IX_operational_events_occurred
        ON dbo.operational_events (
            occurred_at DESC,
            operational_event_id DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_operational_events_severity_occurred'
      AND object_id = OBJECT_ID(
          'dbo.operational_events'
      )
)
BEGIN
    CREATE INDEX IX_operational_events_severity_occurred
        ON dbo.operational_events (
            severity,
            occurred_at DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_operational_events_version_occurred'
      AND object_id = OBJECT_ID(
          'dbo.operational_events'
      )
)
BEGIN
    CREATE INDEX IX_operational_events_version_occurred
        ON dbo.operational_events (
            version_id,
            occurred_at DESC
        )
        WHERE version_id IS NOT NULL;
END;
GO