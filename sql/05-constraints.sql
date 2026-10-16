-- Topic 8, script 5: BREAK IT. Each statement below is REJECTED by the database on purpose.
-- Run them ONE AT A TIME and read each error message. Nothing is changed by the failing statements.

USE ProjectHubDb;
GO

-- C1. Duplicate name, different case -> UNIQUE constraint (error 2627).   Our API: 409 Conflict
INSERT INTO dbo.Projects (Name) VALUES (N'MOBILE APP');
GO

-- C2. Task for a project that doesn't exist -> FOREIGN KEY (error 547).   Our API: 404 Not Found
INSERT INTO dbo.Tasks (ProjectId, Title) VALUES (999, N'Ghost task');
GO

-- C3. A status that isn't 0, 1 or 2 -> CHECK constraint (error 547).
INSERT INTO dbo.Tasks (ProjectId, Title, Status) VALUES (1, N'Weird status', 7);
GO

-- C4. Missing required value -> NOT NULL (error 515).                     Our API: 400 (automatic validation)
INSERT INTO dbo.Projects (Name, Description) VALUES (NULL, N'no name');
GO

-- C5. Delete a project that still has tasks -> FOREIGN KEY again (error 547): the tasks would point to nothing.
DELETE FROM dbo.Projects WHERE Id = 1;
GO

-- C6. Surprise: failed inserts still USED UP identity values. This valid insert does NOT get Id 4.
--     Lesson: never assume ids are consecutive. (Then it is deleted again, so the script stays re-runnable.)
INSERT INTO dbo.Projects (Name) OUTPUT INSERTED.Id, INSERTED.Name VALUES (N'Identity gap demo');
DELETE FROM dbo.Projects WHERE Name = N'Identity gap demo';
GO
