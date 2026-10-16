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
