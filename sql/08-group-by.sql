-- Topic 9, script 8: GROUP BY + aggregates = "one row per group" (C#: GroupBy + Count/Sum/Min/Max).
-- Run the queries ONE AT A TIME in DBeaver. Needs 06 (DueDate).

USE ProjectHubDb;
GO

-- G1. Aggregates over the WHOLE table: one row back.
--     COUNT(*) counts rows; COUNT(DueDate) counts only NON-NULL values (6, not 7: task 6 has no due date).
--     LINQ: tasks.Count(), tasks.Count(t => t.DueDate != null), tasks.Min(t => t.CreatedAt), tasks.Max(...)
SELECT COUNT(*)       AS AllTasks,
       COUNT(DueDate) AS TasksWithDueDate,
       MIN(CreatedAt) AS FirstCreated,
       MAX(CreatedAt) AS LastCreated
FROM dbo.Tasks;

-- G2. GROUP BY one column: how many tasks in each status.
--     RULE: every column in SELECT is either in GROUP BY or inside an aggregate (COUNT, SUM, MIN, MAX, AVG).
--     LINQ: tasks.GroupBy(t => t.Status).Select(g => new { Status = g.Key, Tasks = g.Count() })
SELECT Status, COUNT(*) AS Tasks
FROM dbo.Tasks
GROUP BY Status
ORDER BY Status;

-- G3. THE COUNT(*) TRAP with a LEFT JOIN: tasks per project.
--     "Internal tools" has no tasks, but its LEFT JOIN row (with NULLs) is still a ROW, so COUNT(*) says 1.
SELECT p.Name, COUNT(*) AS Tasks_WRONG, COUNT(t.Id) AS Tasks_RIGHT
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
GROUP BY p.Id, p.Name
ORDER BY p.Name;

-- G4. HAVING = WHERE for GROUPS. Projects with MORE THAN 2 tasks that aren't Done.
--     WHERE filters ROWS before grouping (drop Done tasks), HAVING filters GROUPS after counting.
--     LINQ: tasks.Where(t => t.Status != Done).GroupBy(t => t.ProjectId).Where(g => g.Count() > 2)
--     (WHERE COUNT(*) > 2 is an ERROR: when WHERE runs, nothing has been counted yet.)
SELECT p.Name, COUNT(*) AS OpenTasks
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId
WHERE t.Status <> 2
GROUP BY p.Id, p.Name
HAVING COUNT(*) > 2;

-- REPORT 2: TASKS PER PROJECT. One row per project (including projects with NO tasks), with a count per status.
--   * LEFT JOIN keeps "Internal tools"; COUNT(t.Id) gives it 0 (G3).
--   * CASE WHEN ... THEN 1 ELSE 0 END turns "is this task Todo?" into 1 or 0; SUM adds them up.
--     This is "conditional aggregation": several counts in ONE pass over the rows.
--     For "Internal tools" t.Status is NULL, so every CASE gives 0 (the ELSE).
--   * Overdue uses the same rule as REPORT 1 (past due, not Done).
--   * The API version comes in Topic 11 (EF Core GroupBy, or a projection with t.Count(...)).
SELECT p.Id,
       p.Name,
       COUNT(t.Id)                                          AS TotalTasks,
       SUM(CASE WHEN t.Status = 0 THEN 1 ELSE 0 END)        AS Todo,
       SUM(CASE WHEN t.Status = 1 THEN 1 ELSE 0 END)        AS InProgress,
       SUM(CASE WHEN t.Status = 2 THEN 1 ELSE 0 END)        AS Done,
       SUM(CASE WHEN t.DueDate < SYSUTCDATETIME() AND t.Status <> 2 THEN 1 ELSE 0 END) AS Overdue
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
GROUP BY p.Id, p.Name
ORDER BY p.Name;
