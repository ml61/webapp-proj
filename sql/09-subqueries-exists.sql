-- Topic 9, script 9: subqueries (a query inside a query) and EXISTS.
-- Run the queries ONE AT A TIME in DBeaver. Needs 06 (DueDate).

USE ProjectHubDb;
GO

-- S1. Scalar subquery: returns ONE value, used like a constant. The newest task(s):
--     the inner query runs, gives one date, the outer query compares with it.
--     LINQ: var newest = tasks.Max(t => t.CreatedAt); tasks.Where(t => t.CreatedAt == newest)
SELECT Id, Title, CreatedAt
FROM dbo.Tasks
WHERE CreatedAt = (SELECT MAX(CreatedAt) FROM dbo.Tasks);

-- S2. IN (subquery): the inner query returns a LIST. Projects that have at least one Done task.
--     LINQ: var ids = tasks.Where(t => t.Status == Done).Select(t => t.ProjectId); projects.Where(p => ids.Contains(p.Id))
SELECT Id, Name
FROM dbo.Projects
WHERE Id IN (SELECT ProjectId FROM dbo.Tasks WHERE Status = 2)
ORDER BY Id;

-- S3. EXISTS: "is there AT LEAST ONE matching row?" -> true/false. Projects that have open (not Done) tasks.
--     The inner query mentions p.Id from the OUTER query: a CORRELATED subquery, checked per project.
--     SELECT 1 is a convention: EXISTS only cares whether a row exists, not what's in it.
--     The database can stop at the FIRST match (it doesn't count them all).
--     LINQ: projects.Where(p => tasks.Any(t => t.ProjectId == p.Id && t.Status != Done))  -> EF generates EXISTS
SELECT p.Id, p.Name
FROM dbo.Projects AS p
WHERE EXISTS (SELECT 1 FROM dbo.Tasks AS t WHERE t.ProjectId = p.Id AND t.Status <> 2)
ORDER BY p.Id;

-- S4. NOT EXISTS: projects WITHOUT any task. ("Internal tools")
--     LINQ: projects.Where(p => !tasks.Any(t => t.ProjectId == p.Id))
SELECT p.Id, p.Name
FROM dbo.Projects AS p
WHERE NOT EXISTS (SELECT 1 FROM dbo.Tasks AS t WHERE t.ProjectId = p.Id);

--     The same question with LEFT JOIN + IS NULL (also common; same result):
SELECT p.Id, p.Name
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
WHERE t.Id IS NULL;

-- S5. THE NOT IN TRAP: a NULL in the list makes NOT IN return NOTHING.
--     Question: "tasks whose due date is NOT one of the due dates of project 2's tasks".
--     Project 2's due dates are (2026-09-30, NULL, 2026-10-10). Task 6's NULL is in the list.
--     "x NOT IN (a, NULL)" means "x <> a AND x <> NULL", and "x <> NULL" is UNKNOWN -> never TRUE -> 0 rows.
SELECT Id, Title, DueDate
FROM dbo.Tasks
WHERE DueDate NOT IN (SELECT DueDate FROM dbo.Tasks WHERE ProjectId = 2);

--     NOT EXISTS has no such trap: it only asks "is there a matching row?". 4 rows (tasks 1-4, project 1).
--     (Task 6 itself isn't listed: its own DueDate is NULL, and NULL = anything is never TRUE.)
SELECT t.Id, t.Title, t.DueDate
FROM dbo.Tasks AS t
WHERE t.DueDate IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dbo.Tasks AS t2 WHERE t2.ProjectId = 2 AND t2.DueDate = t.DueDate)
ORDER BY t.Id;
