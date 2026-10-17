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
