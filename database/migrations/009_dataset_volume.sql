IF OBJECT_ID(
    'dbo.dataset_volume_policies',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.dataset_volume_policies (
        volume_policy_id BIGINT
            IDENTITY(1,1)
            NOT NULL
            PRIMARY KEY,

        catalog_id INT NOT NULL,

        drop_threshold_pct DECIMAL(9,4)
            NOT NULL,

        spike_threshold_pct DECIMAL(9,4)
            NOT NULL,

        is_enabled BIT
            NOT NULL
            CONSTRAINT DF_dataset_volume_policies_enabled
            DEFAULT 1,

        created_at DATETIME2
            NOT NULL
            CONSTRAINT DF_dataset_volume_policies_created
            DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2
            NOT NULL
            CONSTRAINT DF_dataset_volume_policies_updated
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_dataset_volume_policies_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT UQ_dataset_volume_policies_catalog
            UNIQUE (catalog_id),

        CONSTRAINT CK_dataset_volume_policies_drop
            CHECK (
                drop_threshold_pct > 0
                AND drop_threshold_pct <= 100
            ),

        CONSTRAINT CK_dataset_volume_policies_spike
            CHECK (
                spike_threshold_pct > 0
            )
    );
END;

GO


IF OBJECT_ID(
    'dbo.dataset_volume_history',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.dataset_volume_history (
        volume_check_id BIGINT
            IDENTITY(1,1)
            NOT NULL
            PRIMARY KEY,

        volume_policy_id BIGINT NOT NULL,

        catalog_id INT NOT NULL,

        ingestion_event_id BIGINT NOT NULL,
        version_id INT NOT NULL,

        baseline_ingestion_event_id BIGINT NULL,
        baseline_version_id INT NULL,

        baseline_row_count INT NULL,
        current_row_count INT NOT NULL,

        drop_threshold_pct DECIMAL(9,4)
            NOT NULL,

        spike_threshold_pct DECIMAL(9,4)
            NOT NULL,

        row_change_pct DECIMAL(19,4) NULL,

        volume_status NVARCHAR(30)
            NOT NULL,

        checked_at DATETIME2
            NOT NULL
            CONSTRAINT DF_dataset_volume_history_checked
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_dataset_volume_history_policy
            FOREIGN KEY (volume_policy_id)
            REFERENCES dbo.dataset_volume_policies(
                volume_policy_id
            ),

        CONSTRAINT FK_dataset_volume_history_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_dataset_volume_history_ingestion
            FOREIGN KEY (ingestion_event_id)
            REFERENCES dbo.ingestion_history(
                ingestion_event_id
            ),

        CONSTRAINT FK_dataset_volume_history_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT FK_dataset_volume_history_baseline_ingestion
            FOREIGN KEY (baseline_ingestion_event_id)
            REFERENCES dbo.ingestion_history(
                ingestion_event_id
            ),

        CONSTRAINT FK_dataset_volume_history_baseline_version
            FOREIGN KEY (baseline_version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT UQ_dataset_volume_history_policy_ingestion
            UNIQUE (
                volume_policy_id,
                ingestion_event_id
            ),

        CONSTRAINT CK_dataset_volume_history_status
            CHECK (
                volume_status IN (
                    'NORMAL',
                    'DROP',
                    'SPIKE',
                    'NO_BASELINE'
                )
            ),

        CONSTRAINT CK_dataset_volume_history_current_rows
            CHECK (
                current_row_count >= 0
            ),

        CONSTRAINT CK_dataset_volume_history_baseline_rows
            CHECK (
                baseline_row_count IS NULL
                OR baseline_row_count >= 0
            )
    );
END;

GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name =
        'IX_dataset_volume_history_catalog_checked'
      AND object_id =
        OBJECT_ID(
            'dbo.dataset_volume_history'
        )
)
BEGIN
    CREATE INDEX
        IX_dataset_volume_history_catalog_checked
    ON dbo.dataset_volume_history (
        catalog_id,
        checked_at DESC
    );
END;

GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name =
        'IX_dataset_volume_history_status_checked'
      AND object_id =
        OBJECT_ID(
            'dbo.dataset_volume_history'
        )
)
BEGIN
    CREATE INDEX
        IX_dataset_volume_history_status_checked
    ON dbo.dataset_volume_history (
        volume_status,
        checked_at DESC
    );
END;

GO