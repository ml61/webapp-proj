-- Topic 8, script 4: the ten queries. Run them ONE AT A TIME and look at each result.
-- Each one shows the LINQ (Topic 2) or API endpoint (Topic 6) it corresponds to.
-- Safe to run again: Q8 inserts 'Docs portal', Q9 renames it, Q10 deletes it.

USE ProjectHubDb;
GO

-- Q1. Everything from one table.                      API: GET /api/projects
SELECT * FROM dbo.Projects;

-- Q2. One row by its key, only some columns.          API: GET /api/projects/1
--     LINQ: projects.Where(p => p.Id == 1).Select(p => new { p.Id, p.Name, p.Description })
SELECT Id, Name, Description
FROM dbo.Projects
WHERE Id = 1;

-- Q3. Filter with several conditions: open tasks of project 1.
--     LINQ: tasks.Where(t => t.ProjectId == 1 && t.Status != TaskItemStatus.Done)
--     SQL: AND / OR / NOT, = and <> (not ==, not !=), IN (0, 1) for "one of these".
SELECT Id, Title, Status
FROM dbo.Tasks
WHERE ProjectId = 1 AND Status <> 2;

-- Q4. Sort: newest first, ties by title A-Z.
--     LINQ: tasks.OrderByDescending(t => t.CreatedAt).ThenBy(t => t.Title)
SELECT Id, Title, CreatedAt
FROM dbo.Tasks
ORDER BY CreatedAt DESC, Title ASC;

-- Q5. Paging: page 2 with 3 rows per page.
--     LINQ: tasks.OrderBy(t => t.Id).Skip(3).Take(3)       (OFFSET/FETCH requires ORDER BY)
SELECT Id, Title
FROM dbo.Tasks
ORDER BY Id
OFFSET 3 ROWS FETCH NEXT 3 ROWS ONLY;

-- Q6. Text search: names containing "app". % = any characters.
--     LINQ: projects.Where(p => p.Name.Contains("app"))   (case-insensitive here: default collation)
SELECT Id, Name
FROM dbo.Projects
WHERE Name LIKE N'%app%';

-- Q7. NULL: projects WITHOUT a description. Use IS NULL.
--     LINQ: projects.Where(p => p.Description == null)
SELECT Id, Name
FROM dbo.Projects
WHERE Description IS NULL;

-- Q7b. The classic trap: "= NULL" NEVER matches (0 rows), because NULL means "unknown",
--      and "unknown = unknown" is not true.
SELECT Id, Name
FROM dbo.Projects
WHERE Description = NULL;

-- Q8. INSERT a row and get the generated values back.  API: POST /api/projects
--     OUTPUT INSERTED.* returns the new row, like the 201 response body.
INSERT INTO dbo.Projects (Name, Description)
OUTPUT INSERTED.Id, INSERTED.Name, INSERTED.CreatedAt
VALUES (N'Docs portal', N'Public API docs');

-- Q9. UPDATE: ALWAYS with a WHERE. Run the SELECT with the same WHERE first to see what you will change.
--     API: PUT /api/projects/{id}
SELECT Id, Name, Description FROM dbo.Projects WHERE Name = N'Docs portal';

UPDATE dbo.Projects
SET Name = N'Docs portal v2', Description = N'Renamed'
WHERE Name = N'Docs portal';

SELECT Id, Name, Description FROM dbo.Projects WHERE Name = N'Docs portal v2';

-- Q10. DELETE: also ALWAYS with a WHERE.                API: DELETE /api/projects/{id}
DELETE FROM dbo.Projects
WHERE Name = N'Docs portal v2';

-- Back to the 3 seed projects. No ORDER BY here, so the row order is NOT guaranteed
-- (in the cloud test they came back as 3, 2, 1). Need an order? Always write ORDER BY.
SELECT Id, Name FROM dbo.Projects;
