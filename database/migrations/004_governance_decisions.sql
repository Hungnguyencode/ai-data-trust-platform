IF OBJECT_ID(
    'dbo.governance_decisions',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.governance_decisions (
        governance_id BIGINT IDENTITY(1,1)
            NOT NULL PRIMARY KEY,

        catalog_id INT NOT NULL,
        version_id INT NOT NULL,
        validation_id BIGINT NOT NULL,

        policy_version NVARCHAR(50) NOT NULL,

        decision NVARCHAR(30) NOT NULL,
        reason NVARCHAR(500) NOT NULL,

        promotion_eligible BIT NOT NULL,

        trust_score DECIMAL(6,2) NOT NULL,
        validation_status NVARCHAR(20) NOT NULL,
        privacy_status NVARCHAR(20) NOT NULL,

        blocking_issue_count INT NOT NULL
            CONSTRAINT DF_governance_blocking_issue_count
            DEFAULT 0,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_governance_created_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_governance_catalog
            FOREIGN KEY (catalog_id)
            REFERENCES dbo.dataset_catalog(catalog_id),

        CONSTRAINT FK_governance_version
            FOREIGN KEY (version_id)
            REFERENCES dbo.dataset_versions(version_id),

        CONSTRAINT FK_governance_validation
            FOREIGN KEY (validation_id)
            REFERENCES dbo.validation_history(validation_id),

        CONSTRAINT CK_governance_decision
            CHECK (
                decision IN (
                    'APPROVED',
                    'REVIEW_REQUIRED',
                    'REJECTED'
                )
            ),

        CONSTRAINT CK_governance_validation_status
            CHECK (
                validation_status IN (
                    'ACCEPTED',
                    'REJECTED'
                )
            ),

        CONSTRAINT CK_governance_privacy_status
            CHECK (
                privacy_status IN (
                    'LOW',
                    'MEDIUM',
                    'HIGH',
                    'CRITICAL'
                )
            ),

        CONSTRAINT CK_governance_trust_score
            CHECK (
                trust_score >= 0
                AND trust_score <= 100
            ),

        CONSTRAINT CK_governance_blocking_count
            CHECK (
                blocking_issue_count >= 0
            ),

        CONSTRAINT UQ_governance_version_validation_policy
            UNIQUE (
                version_id,
                validation_id,
                policy_version
            )
    );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_governance_catalog_created'
      AND object_id = OBJECT_ID(
          'dbo.governance_decisions'
      )
)
BEGIN
    CREATE INDEX IX_governance_catalog_created
        ON dbo.governance_decisions (
            catalog_id,
            created_at DESC
        );
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_governance_version_created'
      AND object_id = OBJECT_ID(
          'dbo.governance_decisions'
      )
)
BEGIN
    CREATE INDEX IX_governance_version_created
        ON dbo.governance_decisions (
            version_id,
            created_at DESC
        );
END;
GO