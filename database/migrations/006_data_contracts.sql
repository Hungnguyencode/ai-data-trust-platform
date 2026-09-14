IF OBJECT_ID(
    'dbo.data_contracts',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.data_contracts (
        contract_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,
        contract_version INT NOT NULL,

        contract_name NVARCHAR(255) NOT NULL,

        enforcement_mode NVARCHAR(20) NOT NULL
            CONSTRAINT DF_data_contracts_enforcement_mode
            DEFAULT 'BLOCK',

        is_active BIT NOT NULL
            CONSTRAINT DF_data_contracts_is_active
            DEFAULT 1,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_data_contracts_created_at
            DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_data_contracts_updated_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_data_contracts_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT UQ_data_contracts_version
            UNIQUE (
                catalog_id,
                contract_version
            ),

        CONSTRAINT CK_data_contracts_version
            CHECK (
                contract_version > 0
            ),

        CONSTRAINT CK_data_contracts_enforcement_mode
            CHECK (
                enforcement_mode IN (
                    'BLOCK',
                    'WARN'
                )
            )
    );
END;
GO


IF OBJECT_ID(
    'dbo.data_contract_columns',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.data_contract_columns (
        contract_column_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        contract_id BIGINT NOT NULL,

        column_name NVARCHAR(255) NOT NULL,
        expected_type NVARCHAR(50) NOT NULL,

        is_required BIT NOT NULL
            CONSTRAINT DF_data_contract_columns_required
            DEFAULT 1,

        is_nullable BIT NOT NULL
            CONSTRAINT DF_data_contract_columns_nullable
            DEFAULT 1,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_data_contract_columns_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_data_contract_columns_contract
            FOREIGN KEY (contract_id)
            REFERENCES dbo.data_contracts(contract_id),

        CONSTRAINT UQ_data_contract_columns_name
            UNIQUE (
                contract_id,
                column_name
            ),

        CONSTRAINT CK_data_contract_columns_type
            CHECK (
                expected_type IN (
                    'NUMERIC',
                    'CATEGORICAL',
                    'DATETIME',
                    'BOOLEAN',
                    'TEXT'
                )
            )
    );
END;
GO


IF OBJECT_ID(
    'dbo.contract_validation_history',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.contract_validation_history (
        contract_validation_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        contract_id BIGINT NOT NULL,
        catalog_id INT NOT NULL,
        version_id INT NOT NULL,

        validation_status NVARCHAR(30) NOT NULL,

        missing_required_count INT NOT NULL
            CONSTRAINT DF_contract_validation_missing
            DEFAULT 0,

        unexpected_column_count INT NOT NULL
            CONSTRAINT DF_contract_validation_unexpected
            DEFAULT 0,

        type_mismatch_count INT NOT NULL
            CONSTRAINT DF_contract_validation_type
            DEFAULT 0,

        nullability_violation_count INT NOT NULL
            CONSTRAINT DF_contract_validation_nullability
            DEFAULT 0,

        violation_count INT NOT NULL
            CONSTRAINT DF_contract_validation_total
            DEFAULT 0,

        validated_at DATETIME2 NOT NULL
            CONSTRAINT DF_contract_validation_validated_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_contract_validation_contract
            FOREIGN KEY (contract_id)
            REFERENCES dbo.data_contracts(contract_id),

        CONSTRAINT FK_contract_validation_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_contract_validation_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT CK_contract_validation_status
            CHECK (
                validation_status IN (
                    'COMPATIBLE',
                    'BREAKING'
                )
            ),

        CONSTRAINT CK_contract_validation_counts
            CHECK (
                missing_required_count >= 0
                AND unexpected_column_count >= 0
                AND type_mismatch_count >= 0
                AND nullability_violation_count >= 0
                AND violation_count >= 0
            )
    );
END;
GO


IF OBJECT_ID(
    'dbo.contract_violations',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.contract_violations (
        violation_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        contract_validation_id BIGINT NOT NULL,

        column_name NVARCHAR(255) NULL,

        violation_type NVARCHAR(40) NOT NULL,

        expected_value NVARCHAR(255) NULL,
        actual_value NVARCHAR(255) NULL,

        message NVARCHAR(1000) NOT NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_contract_violations_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_contract_violations_validation
            FOREIGN KEY (contract_validation_id)
            REFERENCES dbo.contract_validation_history(
                contract_validation_id
            ),

        CONSTRAINT CK_contract_violations_type
            CHECK (
                violation_type IN (
                    'MISSING_REQUIRED_COLUMN',
                    'UNEXPECTED_COLUMN',
                    'TYPE_MISMATCH',
                    'NULLABILITY_VIOLATION'
                )
            )
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_data_contracts_catalog_active'
      AND object_id = OBJECT_ID(
          'dbo.data_contracts'
      )
)
BEGIN
    CREATE INDEX IX_data_contracts_catalog_active
        ON dbo.data_contracts (
            catalog_id,
            is_active,
            contract_version DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_contract_validation_version'
      AND object_id = OBJECT_ID(
          'dbo.contract_validation_history'
      )
)
BEGIN
    CREATE INDEX IX_contract_validation_version
        ON dbo.contract_validation_history (
            version_id,
            validated_at DESC
        );
END;
GO