# Topic 9: notes for the study book (questions, corrections, requests)

- Build: sql/06-add-due-date.sql (ALTER TABLE ADD DueDate DATETIME2 NULL, guarded by COL_LENGTH; UPDATE due dates:
  tasks 2, 5, 7 overdue; 1, 4 past but Done; 3 due 2027; 6 NULL), 07-joins.sql (J1 INNER, J2 LEFT, J3a/J3b
  ON-vs-WHERE trap, J4 by project name, REPORT 1 overdue), 08-group-by.sql (G1 aggregates, G2 per status, G3
  COUNT(*) trap, G4 HAVING, REPORT 2 tasks per project with conditional aggregation), 09-subqueries-exists.sql
  (S1 scalar, S2 IN, S3 EXISTS, S4 NOT EXISTS + LEFT JOIN IS NULL, S5 NOT IN NULL trap + NOT EXISTS fix),
  10-transactions.sql (T1 BEGIN/ROLLBACK delete project 1 + tasks, T2 XACT_ABORT OFF trap XACT_STATE 1, T3 XACT_ABORT
  ON + TRY/CATCH XACT_STATE -1, final check 0 demo projects). Added to the /sql/ solution folder.
- DueDate is SQL-only for now. Decision: add DueDate to the C# TaskItem entity in Topic 10 (EF migration creates
  the schema from the entities), not now (keeps topic 9 SQL-only).
- Real run (cloud, SQL Server 2025, run-sql.sh after a fresh 01-03): docs/studybooks/notes/09-sql-run.txt. Re-run of
  06-10 gave identical output (except DaysOverdue, which depends on today) -> all re-runnable.
- My own mistake while building: first version of T2 let the 547 error escape; run-sql.sh uses sqlcmd -b, so it
  stopped there and T3 never ran. Fix: T2 also catches its error (TRY/CATCH) and shows XACT_STATE() = 1, which makes
  the T2 vs T3 contrast (1 vs -1) visible. Lesson: -b = "stop on the first error" (good for setup, bad for demos).
- Blocking experiment (two sqlcmd sessions): docs/studybooks/notes/09-blocking.txt. READ_COMMITTED_SNAPSHOT is OFF
  (is_read_committed_snapshot_on = 0, on-prem default; Azure SQL has it ON). Session 77 UPDATE project 1 in an open
  transaction; session 78 SELECT project 1 -> LCK_M_S wait -> with LOCK_TIMEOUT 3000: Msg 1222 "Lock request time
  out period exceeded"; SELECT project 2 answered immediately (row lock). sys.dm_exec_requests showed 78 blocked by
  77. Side note: sqlcmd's simple SELECT was auto-parameterized by the server: "(@1 tinyint)SELECT ... WHERE [Id]=@1".
- DEBUG task 5 expected answer verified: Mobile app 2, Website redesign 1.

## CHECK answers (user's words, round 1) and my corrections
User went straight to the CHECK (section 12); piece-1 quiz and DEBUG tasks not answered.
1. "join is needed for launching 2 tables for retrieving info in one go. without it DB would need to scan fully one
   table, then go to 2nd, scan it and then match with 1st one." -> "in one go" right; the "without it" part is wrong:
   scanning both tables and matching IS what a join does inside (hash join), or it uses the IX_Tasks_ProjectId
   index. Without a JOIN the alternative is in YOUR code: N+1 queries (1 for tasks + 1 per task for its project) or
   duplicated data (ProjectName copied into every task). Reason it's needed: normalization, each fact stored once.
2. "inner join - when I need only 'truthy' rows; left join - all rows" -> half. INNER = rows with a match on BOTH
   sides; LEFT = ALL rows of the LEFT table (not of both), NULLs where no match. Missing example: tasks with project
   names (INNER) vs report per project incl. Internal tools with 0 tasks (LEFT).
3. "where removes a row where status is null; condition belongs to the join itself" -> right (in ON). Precise: the
   unmatched row has Status NULL, NULL <> 2 is UNKNOWN, WHERE keeps only TRUE.
4. "* - all rows, even unreal ones (falsy); t.id - all valid truthy rows" -> idea right, wording dangerous:
   COUNT(col) skips only NULL, NOT JS-falsy values (0, '' are counted). COUNT(*) counts the NULL-filled row a LEFT
   JOIN creates.
5. "having is where but for groups" -> right. + WHERE filters rows BEFORE grouping, can't use aggregates.
6. "exists checks if something exists in a list; Any(); NOT IN doesn't work if any value can be NULL" -> right.
   Precise: "in a subquery's rows", stops at the first match, usually correlated (uses p.Id from outside).
7. "protects not finishing action (deleting project requires deleting tasks first, connection problem in between ->
   project without tasks instead of fully removed project); no half-jobs" -> good: atomicity with our example.
   Missing: ISOLATION -- other sessions don't see the half-done state (they wait on locks, READ COMMITTED).
8. "no, we need to rollback in catch" -> half. "No" correct. Full pattern: SET XACT_ABORT ON (error dooms the whole
   transaction, XACT_STATE -1) + TRY/CATCH + IF @@TRANCOUNT > 0 ROLLBACK + THROW (re-raise, like C# throw;).
   Without THROW the caller thinks it succeeded.
9. "because they lock, other sessions are waiting" -> right. + locks held until COMMIT/ROLLBACK -> API requests hang
   or time out (blocking lab: Msg 1222); never wait for a user / HTTP call inside a transaction.
10. "commiting them" -> too vague. SaveChanges wraps ALL pending changes (inserts/updates/deletes) in ONE transaction
   automatically: all saved or none + an exception. Each SaveChanges call = its own transaction; several calls as
   one unit -> Database.BeginTransactionAsync() + CommitAsync().
- Re-check (round 2): a) "JOIN so we receive data matched from 2 tables in one query; without it WE would query one
  table and then query per row to match with the other table (tasks-project)" -> right (= N+1). b) "the SELECT waits
  for the transaction to finish (committed or rolled back)" -> right; + it waits on the LOCK; after ROLLBACK it sees
  the old row, after COMMIT "not found"; may time out (1222). c) "nothing saved, exception" -> right.
- DEBUG task 5 not answered by the user; model answer given (JOIN + WHERE overdue + GROUP BY + HAVING COUNT(*) >= 1;
  Mobile app 2, Website redesign 1). Follow-up point: HAVING is redundant there (INNER JOIN + WHERE -> every group
  has >= 1 row); it matters with a LEFT JOIN or a higher threshold.
- Topic 9 checkpoint passed.
