-- Topic 9, script 6: a SCHEMA CHANGE on a table that already has data (what an EF Core migration does, Topic 10).
-- Adds Tasks.DueDate (nullable: not every task has a deadline) and gives the sample tasks due dates.
-- Run it ONCE after 01-03, from the terminal:  ./scripts/run-sql.sh sql/06-add-due-date.sql
-- Safe to run again: the column is only added if it's missing, and the UPDATEs just set the same values again.
-- If you re-run 02 + 03 later (fresh tables, no DueDate), run 06 again after them.

USE ProjectHubDb;
GO

-- COL_LENGTH returns NULL when the column doesn't exist.
IF COL_LENGTH(N'dbo.Tasks', N'DueDate') IS NULL
    ALTER TABLE dbo.Tasks ADD DueDate DATETIME2(7) NULL;
GO

-- Due dates chosen so the reports have something to show (today is mid-October 2026):
--   past + not Done   -> overdue (tasks 2, 5, 7)
--   past + Done       -> NOT overdue (tasks 1, 4): finished work is never late
--   future            -> not overdue yet (task 3)
--   NULL              -> no deadline (task 6): the NULL trap again
UPDATE dbo.Tasks SET DueDate = '2026-09-10T17:00:00' WHERE Id = 1;   -- Design mockups      (Done)
UPDATE dbo.Tasks SET DueDate = '2026-10-01T17:00:00' WHERE Id = 2;   -- Build landing page  (InProgress)
UPDATE dbo.Tasks SET DueDate = '2027-01-15T17:00:00' WHERE Id = 3;   -- SEO audit           (Todo)
UPDATE dbo.Tasks SET DueDate = '2026-09-05T17:00:00' WHERE Id = 4;   -- Write copy          (Done)
UPDATE dbo.Tasks SET DueDate = '2026-09-30T17:00:00' WHERE Id = 5;   -- Login screen        (InProgress)
UPDATE dbo.Tasks SET DueDate = NULL                  WHERE Id = 6;   -- Push notifications  (Todo)
UPDATE dbo.Tasks SET DueDate = '2026-10-10T17:00:00' WHERE Id = 7;   -- App store listing   (Todo)
GO

-- Check: the new column, filled.
SELECT Id, Title, Status, DueDate FROM dbo.Tasks ORDER BY Id;
