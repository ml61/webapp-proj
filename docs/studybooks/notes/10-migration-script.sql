IF OBJECT_ID(N'[__EFMigrationsHistory]') IS NULL
BEGIN
    CREATE TABLE [__EFMigrationsHistory] (
        [MigrationId] nvarchar(150) NOT NULL,
        [ProductVersion] nvarchar(32) NOT NULL,
        CONSTRAINT [PK___EFMigrationsHistory] PRIMARY KEY ([MigrationId])
    );
END;
GO

BEGIN TRANSACTION;
CREATE TABLE [Projects] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(100) NOT NULL,
    [Description] nvarchar(1000) NULL,
    [CreatedAt] datetime2 NOT NULL,
    CONSTRAINT [PK_Projects] PRIMARY KEY ([Id])
);

CREATE TABLE [Tasks] (
    [Id] int NOT NULL IDENTITY,
    [ProjectId] int NOT NULL,
    [Title] nvarchar(200) NOT NULL,
    [Status] int NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [DueDate] datetime2 NULL,
    CONSTRAINT [PK_Tasks] PRIMARY KEY ([Id]),
    CONSTRAINT [CK_Tasks_Status] CHECK ([Status] IN (0, 1, 2)),
    CONSTRAINT [FK_Tasks_Projects_ProjectId] FOREIGN KEY ([ProjectId]) REFERENCES [Projects] ([Id]) ON DELETE CASCADE
);

IF EXISTS (SELECT * FROM [sys].[identity_columns] WHERE [name] IN (N'Id', N'CreatedAt', N'Description', N'Name') AND [object_id] = OBJECT_ID(N'[Projects]'))
    SET IDENTITY_INSERT [Projects] ON;
INSERT INTO [Projects] ([Id], [CreatedAt], [Description], [Name])
VALUES (1, '2026-09-01T09:00:00.0000000Z', N'New marketing site', N'Website redesign'),
(2, '2026-09-05T09:00:00.0000000Z', NULL, N'Mobile app'),
(3, '2026-09-09T09:00:00.0000000Z', N'Admin dashboards', N'Internal tools');
IF EXISTS (SELECT * FROM [sys].[identity_columns] WHERE [name] IN (N'Id', N'CreatedAt', N'Description', N'Name') AND [object_id] = OBJECT_ID(N'[Projects]'))
    SET IDENTITY_INSERT [Projects] OFF;

IF EXISTS (SELECT * FROM [sys].[identity_columns] WHERE [name] IN (N'Id', N'CreatedAt', N'DueDate', N'ProjectId', N'Status', N'Title') AND [object_id] = OBJECT_ID(N'[Tasks]'))
    SET IDENTITY_INSERT [Tasks] ON;
INSERT INTO [Tasks] ([Id], [CreatedAt], [DueDate], [ProjectId], [Status], [Title])
VALUES (1, '2026-09-02T09:00:00.0000000Z', '2026-09-10T17:00:00.0000000Z', 1, 2, N'Design mockups'),
(2, '2026-09-04T09:00:00.0000000Z', '2026-10-01T17:00:00.0000000Z', 1, 1, N'Build landing page'),
(3, '2026-09-06T09:00:00.0000000Z', '2027-01-15T17:00:00.0000000Z', 1, 0, N'SEO audit'),
(4, '2026-09-03T09:00:00.0000000Z', '2026-09-05T17:00:00.0000000Z', 1, 2, N'Write copy'),
(5, '2026-09-05T09:00:00.0000000Z', '2026-09-30T17:00:00.0000000Z', 2, 1, N'Login screen'),
(6, '2026-09-07T09:00:00.0000000Z', NULL, 2, 0, N'Push notifications'),
(7, '2026-09-08T09:00:00.0000000Z', '2026-10-10T17:00:00.0000000Z', 2, 0, N'App store listing');
IF EXISTS (SELECT * FROM [sys].[identity_columns] WHERE [name] IN (N'Id', N'CreatedAt', N'DueDate', N'ProjectId', N'Status', N'Title') AND [object_id] = OBJECT_ID(N'[Tasks]'))
    SET IDENTITY_INSERT [Tasks] OFF;

CREATE UNIQUE INDEX [IX_Projects_Name] ON [Projects] ([Name]);

CREATE INDEX [IX_Tasks_ProjectId] ON [Tasks] ([ProjectId]);

INSERT INTO [__EFMigrationsHistory] ([MigrationId], [ProductVersion])
VALUES (N'20261017175147_InitialCreate', N'10.0.12');

COMMIT;
GO

