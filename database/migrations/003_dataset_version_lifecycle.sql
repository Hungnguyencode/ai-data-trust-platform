IF COL_LENGTH(
    'dbo.dataset_versions',
    'lifecycle_state'
) IS NULL
BEGIN
    ALTER TABLE dbo.dataset_versions
    ADD lifecycle_state NVARCHAR(30) NOT NULL
        CONSTRAINT DF_dataset_versions_lifecycle_state
        DEFAULT 'NEW';
END;
GO


IF COL_LENGTH(
    'dbo.dataset_versions',
    'promoted_at'
) IS NULL
BEGIN
    ALTER TABLE dbo.dataset_versions
    ADD promoted_at DATETIME2 NULL;
END;
GO


IF COL_LENGTH(
    'dbo.dataset_versions',
    'superseded_at'
) IS NULL
BEGIN
    ALTER TABLE dbo.dataset_versions
    ADD superseded_at DATETIME2 NULL;
END;
GO


IF COL_LENGTH(
    'dbo.dataset_versions',
    'lifecycle_updated_at'
) IS NULL
BEGIN
    ALTER TABLE dbo.dataset_versions
    ADD lifecycle_updated_at DATETIME2 NOT NULL
        CONSTRAINT DF_dataset_versions_lifecycle_updated_at
        DEFAULT SYSUTCDATETIME();
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_dataset_versions_lifecycle_state'
)
BEGIN
    ALTER TABLE dbo.dataset_versions
    ADD CONSTRAINT CK_dataset_versions_lifecycle_state
    CHECK (
        lifecycle_state IN (
            'NEW',
            'VALIDATED',
            'QUARANTINED',
            'ACTIVE',
            'SUPERSEDED'
        )
    );
END;
GO


IF OBJECT_ID(
    'dbo.dataset_version_lifecycle_history',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.dataset_version_lifecycle_history (
        lifecycle_event_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,
        version_id INT NOT NULL,

        from_state NVARCHAR(30) NULL,
        to_state NVARCHAR(30) NOT NULL,

        reason NVARCHAR(500) NULL,

        changed_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_version_lifecycle_history_changed_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_version_lifecycle_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_version_lifecycle_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT CK_version_lifecycle_to_state
            CHECK (
                to_state IN (
                    'NEW',
                    'VALIDATED',
                    'QUARANTINED',
                    'ACTIVE',
                    'SUPERSEDED'
                )
            )
    );
END;
GO


IF OBJECT_ID(
    'dbo.validation_history',
    'U'
) IS NOT NULL
BEGIN
    ;WITH latest_validation AS (
        SELECT
            version_id,
            validation_status,
            ROW_NUMBER() OVER (
                PARTITION BY version_id
                ORDER BY
                    validated_at DESC,
                    validation_id DESC
            ) AS rn
        FROM dbo.validation_history
    )
    UPDATE dv
    SET
        lifecycle_state =
            CASE
                WHEN lv.validation_status = 'ACCEPTED'
                    THEN 'VALIDATED'
                WHEN lv.validation_status = 'REJECTED'
                    THEN 'QUARANTINED'
                ELSE dv.lifecycle_state
            END,
        lifecycle_updated_at = SYSUTCDATETIME()
    FROM dbo.dataset_versions AS dv
    INNER JOIN latest_validation AS lv
        ON dv.version_id = lv.version_id
       AND lv.rn = 1
    WHERE dv.lifecycle_state = 'NEW';
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_dataset_versions_catalog_lifecycle'
      AND object_id = OBJECT_ID(
          'dbo.dataset_versions'
      )
)
BEGIN
    CREATE INDEX IX_dataset_versions_catalog_lifecycle
        ON dbo.dataset_versions (
            catalog_id,
            lifecycle_state,
            version_number DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_dataset_versions_one_active'
      AND object_id = OBJECT_ID(
          'dbo.dataset_versions'
      )
)
BEGIN
    CREATE UNIQUE INDEX UX_dataset_versions_one_active
        ON dbo.dataset_versions (
            catalog_id
        )
        WHERE lifecycle_state = 'ACTIVE';
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_version_lifecycle_history_version'
      AND object_id = OBJECT_ID(
          'dbo.dataset_version_lifecycle_history'
      )
)
BEGIN
    CREATE INDEX IX_version_lifecycle_history_version
        ON dbo.dataset_version_lifecycle_history (
            version_id,
            changed_at DESC
        );
END;
GO