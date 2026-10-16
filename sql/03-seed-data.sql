-- Topic 8, script 3: fill the tables with the same data as src/ProjectHub.Api/Data/SampleData.cs.
-- Run right after 02 (fresh tables), so the generated ids are 1, 2, 3 for projects and 1..7 for tasks.

USE ProjectHubDb;
GO

INSERT INTO dbo.Projects (Name, Description, CreatedAt)
VALUES
    (N'Website redesign', N'New marketing site', '2026-09-01T09:00:00'),
    (N'Mobile app',       NULL,                  '2026-09-05T09:00:00'),
    (N'Internal tools',   N'Admin dashboards',   '2026-09-09T09:00:00');

-- Status: 0 Todo, 1 InProgress, 2 Done
INSERT INTO dbo.Tasks (ProjectId, Title, Status, CreatedAt)
VALUES
    (1, N'Design mockups',     2, '2026-09-02T09:00:00'),
    (1, N'Build landing page', 1, '2026-09-04T09:00:00'),
    (1, N'SEO audit',          0, '2026-09-06T09:00:00'),
    (1, N'Write copy',         2, '2026-09-03T09:00:00'),
    (2, N'Login screen',       1, '2026-09-05T09:00:00'),
    (2, N'Push notifications', 0, '2026-09-07T09:00:00'),
    (2, N'App store listing',  0, '2026-09-08T09:00:00');
GO

-- Check: 3 projects, 7 tasks.
SELECT * FROM dbo.Projects;
SELECT * FROM dbo.Tasks;
