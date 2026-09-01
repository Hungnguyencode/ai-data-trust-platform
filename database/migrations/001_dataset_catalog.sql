IF OBJECT_ID('dbo.dataset_catalog', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dataset_catalog (
        catalog_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        dataset_key NVARCHAR(300) NOT NULL,
        display_name NVARCHAR(255) NOT NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_catalog_created_at
            DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_catalog_updated_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_dataset_catalog_dataset_key
            UNIQUE (dataset_key)
    );
END;
GO


IF OBJECT_ID('dbo.dataset_versions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dataset_versions (
        version_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,
        version_number INT NOT NULL,

        content_sha256 CHAR(64) NOT NULL,

        file_name NVARCHAR(255) NOT NULL,
        file_type NVARCHAR(50) NOT NULL,
        extension NVARCHAR(20) NOT NULL,

        byte_size BIGINT NOT NULL,
        row_count INT NOT NULL,
        column_count INT NOT NULL,

        raw_path NVARCHAR(2048) NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_dataset_versions_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_dataset_versions_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT UQ_dataset_versions_number
            UNIQUE (catalog_id, version_number),

        CONSTRAINT UQ_dataset_versions_content
            UNIQUE (catalog_id, content_sha256)
    );
END;
GO


IF OBJECT_ID('dbo.ingestion_history', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ingestion_history (
        ingestion_event_id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,

        ingestion_id NVARCHAR(36) NOT NULL,

        catalog_id INT NOT NULL,
        version_id INT NOT NULL,

        source_type NVARCHAR(50) NOT NULL,

        ingested_at DATETIMEOFFSET(7) NOT NULL,

        raw_path NVARCHAR(2048) NULL,

        is_new_version BIT NOT NULL
            CONSTRAINT DF_ingestion_history_is_new_version
            DEFAULT 0,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_ingestion_history_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT UQ_ingestion_history_ingestion_id
            UNIQUE (ingestion_id),

        CONSTRAINT FK_ingestion_history_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_ingestion_history_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id)
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_dataset_versions_catalog_created'
      AND object_id = OBJECT_ID('dbo.dataset_versions')
)
BEGIN
    CREATE INDEX IX_dataset_versions_catalog_created
        ON dbo.dataset_versions (
            catalog_id,
            created_at DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_ingestion_history_catalog_ingested'
      AND object_id = OBJECT_ID('dbo.ingestion_history')
)
BEGIN
    CREATE INDEX IX_ingestion_history_catalog_ingested
        ON dbo.ingestion_history (
            catalog_id,
            ingested_at DESC
        );
END;
GO