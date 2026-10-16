# Topic 8: notes for the study book (questions, corrections, requests)

- User is a complete beginner with Docker Desktop and DBeaver (both installed) -> lesson Part B is a click-by-click
  setup guide (Docker Desktop "Engine running", Rosetta on Apple Silicon, docker compose up -d, docker ps,
  docker logs "ready for client connections"; DBeaver: New Database Connection -> SQL Server, localhost:1433, master,
  SQL Server Authentication sa / ProjectHub_Dev123!, driver download, trustServerCertificate=true if certificate error;
  File > Open File, Execute SQL Script vs Execute SQL Statement, Refresh, Data / Constraints / ER Diagram tabs;
  sqlcmd alternative).
- Build: sql/01-create-database.sql, 02-create-tables.sql (Projects/Tasks, IDENTITY, PK, FK, UNIQUE(Name) CI
  collation, CHECK(Status IN (0,1,2)), DEFAULT SYSUTCDATETIME(), IX_Tasks_ProjectId), 03-seed-data.sql (same data as
  SampleData), 04-queries.sql (Q1-Q10 + Q7b), 05-constraints.sql (C1-C6). Added a /sql/ solution folder.
- Real run (cloud, SQL Server 2025, sqlcmd) saved in docs/studybooks/notes/08-sql-run.txt. Notables: Q7b `= NULL` ->
  0 rows; last SELECT without ORDER BY came back 3, 2, 1 (name index) -> order not guaranteed (comment added in 04);
  C1 2627 UQ_Projects_Name (MOBILE APP); C2 547 FK; C3 547 CHECK; C4 515 NULL; C5 547 REFERENCE; C6 identity gap ->
  Id 7. 04 is re-runnable (verified twice).
- Docker daemon in the cloud container had to be restarted manually (session restarted since setup script ran).
- **Question:** "FK is actually an index — the 'id' of a row of another table, so they are linked, right?" ->
  Idea right (an FK column stores the PK value of a row in another table: task 5 ProjectId = 2 -> belongs to project 2;
  JS: tasks[{ id: 5, projectId: 2 }]), word wrong: an FK is not an index. Three separate things on Tasks.ProjectId:
  the COLUMN (stores a number), the FOREIGN KEY (a RULE: must reference an existing project; blocks deleting a
  referenced project), the INDEX (SPEED, IX_Tasks_ProjectId). FK = correctness, index = speed. SQL Server does NOT
  auto-index FKs (it does for PK and UNIQUE) -> we created IX_Tasks_ProjectId ourselves. One-liner: "a foreign key is
  a column holding another table's primary key value, plus a rule that the referenced row must exist."
- **Setup problem (user, DBeaver 26.2.2):** after the driver download, Test Connection -> "Login failed for user 'sa'".
  The driver and network work (a server answered). Diagnosis given: run sqlcmd INSIDE the container
  (`docker exec -it projecthub-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'ProjectHub_Dev123!' -C
  -Q "SELECT @@VERSION"`). Works -> DBeaver side: password typo (Edit Connection F4, retype) or ANOTHER SQL Server on
  port 1433 (`docker ps`, `lsof -i :1433`). Fails too -> the sa password is set only when the data VOLUME is first
  created; an older volume keeps an older password -> `docker compose down -v` + `up -d` (no data lost yet).
  Clue: `docker logs projecthub-sql | grep -i "login failed"`: "Reason: Password did not match" = our container,
  wrong password; no line = DBeaver reached another server. (Outcome: pending user's answer.)
  **Outcome:** it was a password TYPO; Edit Connection (F4) + retyping the password by hand fixed it. Note for the
  book: servers deliberately say only "Login failed" (no reason to the client) so attackers can't tell what was wrong;
  the reason is only in the server log.
- **Setup problem 2 (screenshot):** running 01 -> "Cannot obtain session: No active connection". The tab said
  `<none> 01-create-database.sql`: files opened via File > Open File aren't linked to a connection. Fix: click in the
  editor -> SQL Editor > Set active connection (Cmd+9; or Cmd+3 Find Actions -> "active connection") -> pick
  "master localhost:1433" -> tab becomes `<master> ...`. Once per file. Lesson section 8 step 1 updated.
- **Setup problem 3 (screenshot):** "script 1 did nothing, so script 2 failed" (SQL Error 911: Database 'ProjectHubDb'
  does not exist). Cause: ran 01 with the top ▶ (Execute SQL Statement = only the statement under the cursor) instead
  of the second ▶ with a small + (Execute SQL Script, Option+X = whole file). User confirmed the second button fixed it.
  Also: 01 now has the IF ... CREATE DATABASE on one line + a comment to run it as a script; lesson section 8 says
  which button to use.
- **Setup problem 4 (screenshot):** Q1 `SELECT * FROM dbo.Projects` returned columns but 0 rows -> tables exist
  (02 ran) but are empty: 03 didn't run as a whole script, or 02 was re-run after 03 (02 DROPs and recreates EMPTY
  tables). Fix: run 03 with Execute SQL Script (expect 2 result tabs: 3 projects, 7 tasks), then Q1 again. Rule:
  run 02 -> 03 together, never 02 alone. Navigator: right-click Tables -> Refresh.
- **Setup problem 5 (screenshot):** running 03 -> SQL Error 208 "Invalid object name 'dbo.Tasks'": Projects existed,
  Tasks didn't -> 02 only half-worked in DBeaver. Likely cause (MY script formatting): blank lines INSIDE the CREATE
  TABLE statements; DBeaver can treat a blank line as a statement delimiter and send half a statement (sqlcmd, which I
  tested with, doesn't). Fix: removed blank lines inside statements, added GO between the two CREATE TABLEs, comment in
  02 explaining why; checked all 5 scripts (no blank lines inside parentheses); re-tested 02 + 03 with sqlcmd.
  Lesson: test with the tool the user uses, or write scripts that don't depend on tool-specific splitting.
- **Setup problem 6 (screenshot, after the blank-line fix):** DBeaver Execute SQL Script now sent only
  "CREATE TABLE dbo.Projects" (first line) -> SQL Error 102 Incorrect syntax near 'Projects'. DBeaver's script parser
  splits multi-line CREATE TABLE statements unpredictably (exact cause unknown, can't run DBeaver in the cloud).
  Decision: stop guessing. Setup scripts 01-03 run via sqlcmd inside the container: new tooling script
  scripts/run-sql.sh (docker exec -i ... sqlcmd -C -b -W < file), verified 01-03 run cleanly. DBeaver kept for
  browsing + 04/05 one statement at a time (select the query text first if DBeaver cuts it; run `USE ProjectHubDb`
  first or pick ProjectHubDb in the toolbar database selector). Lesson section 8 rewritten (8.1 terminal, 8.2 DBeaver).
- **Setup problem 7 (screenshot, "omg"):** tables exist in ProjectHubDb but Q1 shows columns and no rows; toolbar
  showed `dbo@master`. Root cause of problems 4-7: the FIRST DBeaver run of 02 failed at `USE ProjectHubDb` (database
  didn't exist yet) but DBeaver CONTINUED in master and created an empty master.dbo.Projects. Since then Q1 read
  master.dbo.Projects (empty) and 03 failed "Invalid object name dbo.Tasks" (master has no Tasks). Fix: Edit
  Connection -> Database: ProjectHubDb (toolbar dbo@ProjectHubDb); drop the stray tables in master via sqlcmd
  (`USE master; DROP TABLE IF EXISTS dbo.Tasks; DROP TABLE IF EXISTS dbo.Projects;`); run-sql.sh 01-03; Q1 again.
  Lesson: always check WHICH DATABASE a query runs in (context first: server, database, build — like topic 5's stale
  build). Lesson section 8.1 updated to point the connection at ProjectHubDb.
- **Setup problem 8 (2 screenshots, "no result still, but there is data"):** the navigator's Projects -> Data tab
  showed 3 rows, but Q1 in the 04 editor showed columns and 0 rows; the toolbar still said `dbo@master`. Why the two
  views disagree: the Data tab reads ProjectHubDb.dbo.Projects (the table you clicked in the tree). The editor runs
  `SELECT * FROM dbo.Projects` in ITS current database, which was still master. master.dbo.Projects (empty) still
  existed, because the stray tables hadn't been dropped yet. Otherwise Q1 would have failed loudly (error 208) instead of
  quietly returning an empty result. Ctrl+Enter ran only Q1, not the `USE ProjectHubDb;` line above it. Editing the
  connection's default database doesn't change editor tabs that are already open. Fix: toolbar `dbo@master` ->
  pick ProjectHubDb / dbo (or run the USE line first); `SELECT DB_NAME();` to check; drop the stray master tables.
  Concepts: two-part name dbo.Projects (schema.table) is resolved inside the CURRENT database. A three-part name
  ProjectHubDb.dbo.Projects (database.schema.table) works from anywhere. In C# the current database comes from the
  connection string's `Database=` part.
