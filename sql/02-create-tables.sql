-- Topic 8, script 2: create the two tables, by hand.
-- Run it with "Execute SQL Script" (the whole file).
-- Safe to run again: it DROPS both tables first, so all their data is deleted. Then run 03 to fill them again.
-- (No blank lines INSIDE a statement: some tools, like DBeaver, can treat a blank line as "end of statement".)

USE ProjectHubDb;
GO

-- Drop in reverse dependency order: Tasks references Projects, so Tasks must go first.
DROP TABLE IF EXISTS dbo.Tasks;
DROP TABLE IF EXISTS dbo.Projects;
GO

-- C#: Entities/Project.cs
CREATE TABLE dbo.Projects
(
    Id          INT            IDENTITY(1, 1) NOT NULL,   -- the database generates 1, 2, 3, ...
    Name        NVARCHAR(100)  NOT NULL,                  -- required string, max 100 (ProjectService.MaxNameLength)
    Description NVARCHAR(1000) NULL,                      -- string? -> NULL allowed
    CreatedAt   DATETIME2(7)   NOT NULL
        CONSTRAINT DF_Projects_CreatedAt DEFAULT SYSUTCDATETIME(),   -- like "= DateTime.UtcNow"
    CONSTRAINT PK_Projects PRIMARY KEY (Id),
    -- The business rule from Topic 3, now enforced by the database itself. The column uses the server's default
    -- case-INsensitive collation, so 'Mobile app' and 'MOBILE APP' count as the same name.
    CONSTRAINT UQ_Projects_Name UNIQUE (Name)
);
GO

-- C#: Entities/TaskItem.cs
CREATE TABLE dbo.Tasks
(
    Id        INT           IDENTITY(1, 1) NOT NULL,
    ProjectId INT           NOT NULL,                     -- which project this task belongs to
    Title     NVARCHAR(200) NOT NULL,
    Status    INT           NOT NULL
        CONSTRAINT DF_Tasks_Status DEFAULT 0,             -- 0 = Todo (TaskItemStatus is an int underneath, Topic 1)
    CreatedAt DATETIME2(7)  NOT NULL
        CONSTRAINT DF_Tasks_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_Tasks PRIMARY KEY (Id),
    -- Foreign key: every task must point to a project that EXISTS.
    CONSTRAINT FK_Tasks_Projects_ProjectId FOREIGN KEY (ProjectId) REFERENCES dbo.Projects (Id),
    -- Only the three TaskItemStatus values: 0 Todo, 1 InProgress, 2 Done.
    CONSTRAINT CK_Tasks_Status CHECK (Status IN (0, 1, 2))
);
GO

-- Index on the foreign key: makes "all tasks of project X" fast (Topic 18 goes deeper).
CREATE INDEX IX_Tasks_ProjectId ON dbo.Tasks (ProjectId);
GO

-- Check: both tables exist (empty for now).
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME;
