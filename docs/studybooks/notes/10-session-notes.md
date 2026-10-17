# Topic 10: notes for the study book (questions, corrections, requests)

- Build (all by me, user reviews): EF Core 10.0.12 (SqlServer + Design), local tool dotnet-ef 10.0.12 in
  dotnet-tools.json (repo root, .NET 10 puts it there, not in .config/). ProjectHubDbContext (DbSets, ConfigureConventions
  with UtcDateTimeConverter for DateTime/DateTime?, Fluent API: HasMaxLength from ProjectRules, unique index on Name,
  HasMany/WithOne/HasForeignKey, CHECK constraint, HasData seed from SampleData as flat anonymous objects).
  ProjectService rewritten for EF (Scoped; Include + ordered Include; AnyAsync name check; Add/modify/Remove +
  SaveChangesAsync; DbUpdateException when SqlException 2601/2627 -> ConflictException). Old service renamed
  InMemoryProjectService (playground 03/04 + DebugLabA use it; playground 03's decorator got the dueDate parameter).
  ProjectRules (MaxName 100, MaxDescription 1000 NEW check, MaxTitle 200 NEW check). ProjectStoreOptions removed
  (simulated latency meaningless now). DueDate added to TaskItem, SampleData (same dates as topic 9's sql/06),
  CreateTaskRequest (optional), TaskResponse. Program.cs: GetConnectionString ?? throw (fail fast), AddDbContext +
  EnableSensitiveDataLogging in Development, AddScoped<IProjectService, ProjectService>. appsettings.Development.json:
  connection string (Database=ProjectHub, TrustServerCertificate=True) + EF command logging at Information.
  .http: create saves {{projectId}} with a Rider response handler (ids no longer predictable).
- Database decision: EF owns a NEW database "ProjectHub"; topics 8-9's hand-made "ProjectHubDb" stays as the SQL
  playground (a migrations-owned schema must never be changed by hand).
- Security: build showed NU1902/NU1903 for System.Security.Cryptography.Pkcs 9.0.11 (transitive via
  Microsoft.Data.SqlClient 6.1.6, found in obj/project.assets.json; `dotnet nuget why` printed nothing). Pinned 10.0.12
  -> still flagged; 10.0.13 -> clean build. Kept a comment in the csproj. (GitHub advisory API blocked in the session,
  so NuGet's own audit was the check.)
- Migration InitialCreate generated: names identical to topic 8's hand-written script (PK_Projects,
  FK_Tasks_Projects_ProjectId, CK_Tasks_Status, IX_Tasks_ProjectId) because I used EF conventions in topic 8.
  Differences: IX_Projects_Name unique INDEX (error 2601) vs UQ_ constraint (2627); ON DELETE CASCADE vs refused
  delete (C5); FK index automatic; no DB default for CreatedAt. Script: notes/10-migration-script.sql (wrapped in
  BEGIN TRANSACTION/COMMIT; IDENTITY_INSERT for seed). After update: IDENT_CURRENT Projects 3, Tasks 7.
- Cloud hiccup: Docker daemon was down again at `database update` (error 35 "server not found"); restarted dockerd +
  compose up -d.
- Real runs: notes/10-api-calls.txt (phase 1, restart, phase 2: persistence verified; new project after delete got
  id 5), notes/10-generated-sql.txt (EF command log: LEFT JOIN for Include, TOP(2) for SingleOrDefault, EXISTS for Any,
  null-parameter condition removed, INSERT OUTPUT INSERTED.Id, UPDATE only changed columns, FindAsync TOP(1), DELETE).
- Race (notes/10-race.txt): 3 x 10 concurrent POSTs; rounds 2-3: 1x201 + 9x409 each; 30 EXISTS checks, 12 INSERTs,
  10 stopped only by the unique index (2601 -> 409). Ids 9 -> 19 (failed inserts used identity values).
  MY mistake while scripting it: a bare `wait` also waited for the background API process -> hung; fixed by waiting
  only for the curl PIDs. (Also: never pkill -f; kill by PID.)
- DEBUG scenarios (notes/10-debug-scenarios.txt): captive dependency (AddSingleton) -> app refuses to start "Cannot
  consume scoped service ProjectHubDbContext from singleton IProjectService" (exit 134); empty DB -> app starts, first
  request 500 "Invalid object name 'Projects'" (208); missing DB -> 500 "Cannot open database ..." (4060);
  string.Equals(..., OrdinalIgnoreCase) in AnyAsync -> 500 InvalidOperationException "could not be translated ...
  Translation of the 'string.Equals' overload with a 'StringComparison' parameter is not supported".
- All 4 playground demos still run after the rename (dotnet run --no-cache).
