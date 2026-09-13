IF OBJECT_ID(
    'dbo.pipeline_runs',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.pipeline_runs (
        pipeline_run_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        dag_id NVARCHAR(250) NOT NULL,
        airflow_run_id NVARCHAR(250) NOT NULL,
        source_path NVARCHAR(2048) NOT NULL,

        run_status NVARCHAR(20) NOT NULL
            CONSTRAINT DF_pipeline_runs_status
            DEFAULT 'RUNNING',

        attempt_count INT NOT NULL
            CONSTRAINT DF_pipeline_runs_attempt_count
            DEFAULT 0,

        catalog_id INT NULL,
        version_id INT NULL,

        validation_status NVARCHAR(20) NULL,
        governance_decision NVARCHAR(30) NULL,
        trust_score DECIMAL(6,2) NULL,
        lifecycle_state NVARCHAR(30) NULL,

        started_at DATETIME2 NOT NULL
            CONSTRAINT DF_pipeline_runs_started_at
            DEFAULT SYSUTCDATETIME(),

        finished_at DATETIME2 NULL,
        duration_ms BIGINT NULL,

        error_type NVARCHAR(255) NULL,
        error_message NVARCHAR(MAX) NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_pipeline_runs_created_at
            DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_pipeline_runs_updated_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_pipeline_runs_airflow_run
            UNIQUE (
                dag_id,
                airflow_run_id
            ),

        CONSTRAINT FK_pipeline_runs_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_pipeline_runs_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT CK_pipeline_runs_status
            CHECK (
                run_status IN (
                    'RUNNING',
                    'SUCCESS',
                    'FAILED'
                )
            ),

        CONSTRAINT CK_pipeline_runs_attempt_count
            CHECK (
                attempt_count >= 0
            ),

        CONSTRAINT CK_pipeline_runs_trust_score
            CHECK (
                trust_score IS NULL
                OR (
                    trust_score >= 0
                    AND trust_score <= 100
                )
            )
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_pipeline_runs_status_started'
      AND object_id = OBJECT_ID(
          'dbo.pipeline_runs'
      )
)
BEGIN
    CREATE INDEX IX_pipeline_runs_status_started
        ON dbo.pipeline_runs (
            run_status,
            started_at DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_pipeline_runs_version_started'
      AND object_id = OBJECT_ID(
          'dbo.pipeline_runs'
      )
)
BEGIN
    CREATE INDEX IX_pipeline_runs_version_started
        ON dbo.pipeline_runs (
            version_id,
            started_at DESC
        )
        WHERE version_id IS NOT NULL;
END;
GO