-- Topic 9, script 7: JOINs = put rows from two tables back together through the foreign key.
-- Run the queries ONE AT A TIME in DBeaver (toolbar must say dbo@ProjectHubDb; check with SELECT DB_NAME();).
-- Needs 06 (DueDate).

USE ProjectHubDb;
GO

-- J1. INNER JOIN: every task WITH its project's name. Only rows that have a match on BOTH sides.
--     t and p are ALIASES (short names for the tables). ON = how rows match: the FK = the PK.
--     LINQ: tasks.Join(projects, t => t.ProjectId, p => p.Id, (t, p) => new { t.Id, t.Title, Project = p.Name })
--     EF Core (Topic 11): tasks.Select(t => new { t.Title, Project = t.Project.Name })  -> generates this JOIN
SELECT t.Id, t.Title, p.Name AS ProjectName
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId
ORDER BY p.Name, t.Id;

-- J2. LEFT JOIN: every PROJECT, with its tasks if it has any.
--     "Internal tools" has no tasks: it still appears, once, with NULL in every task column.
--     (INNER JOIN would drop it, exactly like J1 has no row for it.)
SELECT p.Id AS ProjectId, p.Name, t.Id AS TaskId, t.Title
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
ORDER BY p.Id, t.Id;

-- J3. THE LEFT JOIN TRAP: "every project, with its OPEN tasks".
--     J3a filters in WHERE: WHERE runs AFTER the join, so the NULL row of "Internal tools" fails
--     "t.Status <> 2" (NULL <> 2 is UNKNOWN) and the project disappears. The LEFT JOIN became an INNER JOIN.
SELECT p.Name, t.Title, t.Status
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
WHERE t.Status <> 2
ORDER BY p.Name, t.Title;

--     J3b puts the condition in ON: it decides WHICH TASKS match, and every project is still kept.
SELECT p.Name, t.Title, t.Status
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id AND t.Status <> 2
ORDER BY p.Name, t.Title;

-- J4. Topic 8's promise: Todo tasks of "Mobile app" by NAME, not by the magic number 2.
SELECT t.Id, t.Title, t.CreatedAt
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId
WHERE p.Name = N'Mobile app' AND t.Status = 0
ORDER BY t.CreatedAt;

-- REPORT 1: OVERDUE TASKS. Past the due date, not Done, with the project name, most overdue first.
--   * SYSUTCDATETIME() = "now" in UTC (C#: DateTime.UtcNow). Our dates are UTC too (Topic 1).
--   * DATEDIFF(DAY, a, b) = whole days from a to b.
--   * Task 6 has no due date (NULL): "NULL < now" is UNKNOWN, so it is NOT reported. That's the behavior we want here.
SELECT p.Name AS ProjectName,
       t.Id,
       t.Title,
       t.Status,
       t.DueDate,
       DATEDIFF(DAY, t.DueDate, SYSUTCDATETIME()) AS DaysOverdue
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId
WHERE t.DueDate < SYSUTCDATETIME()
  AND t.Status <> 2
ORDER BY t.DueDate;
