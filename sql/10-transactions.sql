-- Topic 9, script 10: TRANSACTIONS = several statements that succeed or fail TOGETHER.
-- Every block below ends with ROLLBACK, so the script never changes the data (safe to run again).
-- T1: run it ONE STATEMENT AT A TIME in DBeaver (same editor = same connection = same transaction).
-- T2-T3: select the WHOLE block (from SET to END CATCH;) with the mouse, then run it (DBeaver sends exactly the selection),
--        or run the whole file from the terminal: ./scripts/run-sql.sh sql/10-transactions.sql

USE ProjectHubDb;
GO

-- T1. BEGIN TRAN ... ROLLBACK: undo for real.
--     "Delete project 1": its tasks must go first (FK, Topic 8 C5), so it's TWO statements.
--     Without a transaction, a crash between them leaves the tasks deleted and the project still there.
BEGIN TRANSACTION;

SELECT @@TRANCOUNT AS OpenTransactions;                       -- 1: we are inside a transaction

DELETE FROM dbo.Tasks    WHERE ProjectId = 1;                 -- (4 rows affected)
DELETE FROM dbo.Projects WHERE Id = 1;                        -- (1 row affected)

SELECT Id, Name FROM dbo.Projects ORDER BY Id;                -- inside the transaction: project 1 is gone

ROLLBACK TRANSACTION;                                         -- undo BOTH deletes (COMMIT would make them permanent)

SELECT Id, Name FROM dbo.Projects ORDER BY Id;                -- project 1 is back, with its 4 tasks
SELECT COUNT(*) AS TasksOfProject1 FROM dbo.Tasks WHERE ProjectId = 1;
SELECT @@TRANCOUNT AS OpenTransactions;                       -- 0: nothing left open
GO

-- T2. THE TRAP: an error does NOT automatically undo the transaction in SQL Server.
--     By default an error like 547 (CHECK) cancels only THAT STATEMENT. The transaction stays open,
--     and the statements before it are still there, waiting for COMMIT.
--     Create a project and its first task, and the task is invalid (Status 7).
--     TRY/CATCH (like C# try/catch) catches the error so we can look at the state:
--       XACT_STATE() =  1 -> a transaction is open and can still be COMMITTED (dangerous: half the work)
--       XACT_STATE() = -1 -> a transaction is open but doomed: only ROLLBACK is allowed
--       XACT_STATE() =  0 -> no transaction
SET XACT_ABORT OFF;                                           -- the default, written out for the demo
BEGIN TRY
    BEGIN TRANSACTION;
    INSERT INTO dbo.Projects (Name) VALUES (N'Half-created project');
    INSERT INTO dbo.Tasks (ProjectId, Title, Status) VALUES (SCOPE_IDENTITY(), N'Bad task', 7);   -- error 547
    COMMIT TRANSACTION;                                       -- never reached
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           XACT_STATE()   AS XactState,                       -- 1: still committable!
           (SELECT COUNT(*) FROM dbo.Projects WHERE Name = N'Half-created project') AS ProjectStillThere;   -- 1
    -- A COMMIT here would save the project WITHOUT its task: half the work. We undo it:
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
END CATCH;
GO

-- T3. THE CORRECT PATTERN: XACT_ABORT ON + TRY/CATCH + ROLLBACK + THROW.
--     SET XACT_ABORT ON: any runtime error dooms the WHOLE transaction (XACT_STATE() = -1), not just the statement.
--     In CATCH: roll back if still open, then THROW the error again (like C# "throw;") so the caller knows.
--     This is what EF Core's SaveChanges does for you: all changes in one transaction, all or nothing (Topic 10).
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    INSERT INTO dbo.Projects (Name) VALUES (N'All-or-nothing project');
    INSERT INTO dbo.Tasks (ProjectId, Title, Status) VALUES (SCOPE_IDENTITY(), N'Bad task', 7);   -- error 547
    COMMIT TRANSACTION;                                       -- never reached
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber,
           XACT_STATE()   AS XactState,                       -- -1: doomed, only ROLLBACK possible
           ERROR_MESSAGE() AS ErrorMessage;
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    -- In real code the next line is:  THROW;   (re-raise). Left out here so the script continues to the check.
END CATCH;
SET XACT_ABORT OFF;
GO

-- Check: neither demo project exists. Nothing half-done is left behind.
SELECT COUNT(*) AS DemoProjects
FROM dbo.Projects
WHERE Name IN (N'Half-created project', N'All-or-nothing project');
GO
