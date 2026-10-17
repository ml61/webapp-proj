# Lesson 10: EF Core basics: DbContext, DbSet, provider, migrations

**Roadmap:** Week 2, Topic 10. **Time:** about 2–3 h.
**Build:** replace the in-memory storage with SQL Server + EF Core.
**Checkpoint:** the **schema comes from a migration**, and **CRUD persists** (the data survives an API restart).

**What changed in the code** (Rider: `src/ProjectHub.Api`):

| File | Change |
|---|---|
| `Data/ProjectHubDbContext.cs` | **new**: the DbContext. Tables, keys, rules, seed data |
| `Data/UtcDateTimeConverter.cs` | **new**: dates come back from SQL Server as UTC |
| `Data/Migrations/*` | **new, generated** by `dotnet ef migrations add InitialCreate` |
| `Services/ProjectService.cs` | **rewritten**: EF Core instead of a `List` + `lock` |
| `Services/InMemoryProjectService.cs` | the **old** `ProjectService`, renamed. Kept for the playground demos and labs |
| `Services/ProjectRules.cs` | **new**: the name/title/description rules in one place (both services + the DbContext use them) |
| `Program.cs` | `AddDbContext` + `AddScoped<IProjectService, ProjectService>()`. The Topic 7 `ProjectStoreOptions` are gone (there's no simulated latency anymore: the latency is real now) |
| `appsettings.Development.json` | the **connection string**, plus SQL logging |
| `Entities/TaskItem.cs`, `Contracts/*`, `SampleData.cs` | `DueDate` (Topic 9's column, now from C#) |
| `ProjectHub.Api.csproj` | the EF Core packages (+ one security pin, section 9) |
| `dotnet-tools.json` | **new**: the `dotnet-ef` command-line tool, pinned for the repo |
| `ProjectHub.Api.http` | ids are saved in a variable now (they're no longer predictable) |

**What did NOT change: `ProjectsController.cs`** (except passing `DueDate`). It only knows `IProjectService`. Topic 3 promised that an interface lets you swap the implementation without touching the callers. This is the proof: the storage went from a `List` to SQL Server, and the controller didn't notice.

Everything was run in the cloud against SQL Server 2025: the migration, every endpoint, a restart, a 30-request race, and four failure scenarios. Part C has the real output.

---

# Part A: Concepts

## 1. What EF Core is

**EF Core = an ORM (Object-Relational Mapper).** You work with C# objects and LINQ, and EF Core writes the SQL from Topics 8–9 for you.
- **TS analogy:** Prisma, TypeORM, Drizzle. `prisma.project.findMany({ include: { tasks: true } })` ≈ `db.Projects.Include(p => p.Tasks).ToListAsync()`.
- `prisma migrate` ≈ `dotnet ef migrations` + `dotnet ef database update`.

| Piece | What it is | Ours |
|---|---|---|
| **Provider** | the package that speaks one database's SQL dialect | `Microsoft.EntityFrameworkCore.SqlServer` (there are others for PostgreSQL, SQLite, ...) |
| **DbContext** | one "session" with the database: runs queries, **tracks changes**, saves them | `ProjectHubDbContext` |
| **DbSet\<T\>** | one table you can query with LINQ | `db.Projects`, `db.Tasks` |
| **Model** | how classes map to tables: **conventions** + **Fluent API** configuration | `OnModelCreating` |
| **Migrations** | versioned C# files that create or change the schema | `Data/Migrations/` |
| **Change tracker** | remembers loaded/added/removed entities and what changed | used by `SaveChangesAsync` |

**Why use an ORM at all**, if you can write SQL? Less boilerplate: no hand-written mapping of each column to each property. Queries checked by the compiler (rename a property and every query updates). Parameters always used (no SQL injection, Topic 8). One transaction per `SaveChanges` (Topic 9). **The price:** you must know what SQL it generates, or it can be slow (Topic 11's N+1). That's why Topics 8–9 came first.

## 2. The DbContext

```csharp
public class ProjectHubDbContext(DbContextOptions<ProjectHubDbContext> options) : DbContext(options)
{
    public DbSet<Project> Projects => Set<Project>();
    public DbSet<TaskItem> Tasks => Set<TaskItem>();
    ...
}
```
- **`DbContextOptions`** (provider + connection string) arrive through the constructor, via **DI** (Topic 7), from `Program.cs`.
- **`=> Set<Project>()`** instead of `{ get; set; }`: a property that returns EF's set. It avoids the "non-nullable property is not initialized" warning (Topic 1).
- **Registered as Scoped** by `AddDbContext`: **one DbContext per HTTP request**. Why:
  1. A DbContext is **not thread-safe**. Two requests using the same one at the same time corrupt its change tracker.
  2. It **tracks** every entity it loads. A singleton would remember entities forever (stale data, growing memory).
  3. One request = one unit of work: load, change, `SaveChanges`, done.

**Consequence: `ProjectService` must be Scoped too.** As a singleton it would hold one DbContext forever: a **captive dependency** (Topic 7). We tried it, and ASP.NET refused to start (Part C, 12.3).

## 3. The model: conventions + Fluent API

EF Core reads your classes and applies **conventions**, and you configure what it can't guess. Compare with our hand-written `sql/02-create-tables.sql`:

| What | Topic 8 (by hand) | EF Core | How |
|---|---|---|---|
| table names | `Projects`, `Tasks` | `Projects`, `Tasks` | convention: the **DbSet property name** |
| `Id` = primary key + IDENTITY | `INT IDENTITY(1,1)`, `PK_Projects` | the same | convention: a property called `Id` |
| `Name` NOT NULL, `Description` NULL | written by hand | the same | convention: `string` vs `string?` (**nullable reference types**, Topic 1) |
| `NVARCHAR(100)` | written by hand | `HasMaxLength(ProjectRules.MaxNameLength)` | Fluent API. **Without it: `NVARCHAR(MAX)`** |
| enum `Status` | `INT` | `int` | convention |
| FK `Tasks.ProjectId` | `FK_Tasks_Projects_ProjectId` | the **same name** | `HasMany(p => p.Tasks).WithOne().HasForeignKey(t => t.ProjectId)` |
| index on the FK | we had to add `IX_Tasks_ProjectId` ourselves | **created automatically** | EF convention (SQL Server doesn't do it, Topic 8) |
| unique name | `UQ_Projects_Name` (a UNIQUE **constraint**, error **2627**) | `IX_Projects_Name` (a UNIQUE **index**, error **2601**) | `HasIndex(p => p.Name).IsUnique()` |
| delete a project with tasks | **refused** (Topic 8 C5, error 547) | **ON DELETE CASCADE**: the tasks are deleted too | convention for a **required** relationship |
| `CHECK (Status IN (0,1,2))` | `CK_Tasks_Status` | the same | `HasCheckConstraint(...)` |
| `CreatedAt DEFAULT SYSUTCDATETIME()` | in SQL | **no DB default**: C# sets `= DateTime.UtcNow` | a design choice |

The names were the same on purpose: in Topic 8 I used **EF Core's naming conventions**, so this table would line up.

**Fluent API vs attributes.** You can also write `[MaxLength(100)]` on the entity property (data annotations). We use the Fluent API in `OnModelCreating`, so the entities stay plain classes and the database rules live in one file. Both are common. Know that both exist.

## 4. Migrations

**A migration = a C# file describing one schema change**, with `Up()` (apply) and `Down()` (undo). It works like version control for the database schema: it lives in git next to the code that needs it.

```bash
dotnet ef migrations add InitialCreate --project src/ProjectHub.Api --output-dir Data/Migrations
dotnet ef database update --project src/ProjectHub.Api
```
1. **`migrations add`** compares the **model** (your classes + `OnModelCreating`) with the **snapshot** of the previous model (`ProjectHubDbContextModelSnapshot.cs`), and writes the **difference** as a new migration. It doesn't touch the database.
2. **`database update`** connects to the database, reads the table **`__EFMigrationsHistory`** (which migrations already ran), and runs only the **missing** ones. Each migration runs **in a transaction** (Topic 9): all of it, or none of it.

Three generated files:

| File | What | Edit it? |
|---|---|---|
| `20261017175147_InitialCreate.cs` | `Up()` / `Down()`: CreateTable, CreateIndex, InsertData | rarely (e.g. custom SQL). **Never after it's been applied and shared** |
| `...InitialCreate.Designer.cs` | the model as it was at this migration | no |
| `ProjectHubDbContextModelSnapshot.cs` | the **current** model; the next `migrations add` compares against it | no |

**Rules:**
- **The migrations own the schema.** Never change a migrations-managed database by hand (no `ALTER TABLE` in DBeaver). The next migration wouldn't know about it.
- That's why EF Core gets its **own database, `ProjectHub`**. Your hand-made `ProjectHubDb` from Topics 8–9 stays as your SQL playground.
- A mistake in a migration **not yet applied anywhere** → `dotnet ef migrations remove`. Already applied/shared → write a **new** migration that fixes it.
- `dotnet ef migrations script` prints the SQL a migration would run. In real teams, production databases are often updated from such a reviewed script, not by `database update`.

**Seed data** (`HasData` in `OnModelCreating`): becomes `InsertData` in the migration, so the sample projects exist right after `database update`. Seed values must be **fixed**: `DateTime.UtcNow` would change on every `migrations add` and create a new "change" every time. That's why `SampleData` uses fixed dates.

## 5. Configuration: the connection string

```json
"ConnectionStrings": {
  "ProjectHub": "Server=localhost,1433;Database=ProjectHub;User Id=sa;Password=ProjectHub_Dev123!;TrustServerCertificate=True"
}
```
| Part | Means |
|---|---|
| `Server=localhost,1433` | host, port (a **comma** in SQL Server syntax) |
| `Database=ProjectHub` | the **current database** (Topic 8's master trap: without it, you'd land in master) |
| `User Id` / `Password` | SQL authentication (dev only) |
| `TrustServerCertificate=True` | accept the container's self-signed certificate (the DBeaver certificate problem, Topic 8). Local only |

- `builder.Configuration.GetConnectionString("ProjectHub")` reads `ConnectionStrings:ProjectHub`. Missing → we **throw at startup** (fail fast, Topic 7).
- Production: never in `appsettings.json` in git. Use an environment variable `ConnectionStrings__ProjectHub` (Topic 7's double underscore), or a secret store (Topic 19: Key Vault + Managed Identity, no password at all).
- **The database isn't contacted at startup.** A wrong database name or a missing migration shows up only at the **first query**, as a 500 (Part C, 12.4).

## 6. The new ProjectService, piece by piece

### 6.1 LINQ to SQL: IQueryable and deferred execution
```csharp
return await db.Projects
    .Include(p => p.Tasks)
    .OrderBy(p => p.Id)
    .ToListAsync(cancellationToken);
```
- `db.Projects` is an **`IQueryable<Project>`**, not a list. `.Include`, `.OrderBy` and `.Where` only **build a query**. Nothing is sent yet.
- **`ToListAsync()`** (or `SingleOrDefaultAsync`, `AnyAsync`, `FirstOrDefaultAsync`, ...) **translates the whole chain into one SQL statement** and runs it.
- It's **Topic 2's deferred execution**, but instead of running C# loops later, EF translates the expression into SQL. Interview line: **"`IEnumerable` runs in memory; `IQueryable` is translated and runs in the database."**
- **Not everything can be translated.** `string.Equals(a, b, StringComparison.OrdinalIgnoreCase)` has no SQL equivalent → `InvalidOperationException: ... could not be translated` (Part C, 12.5). We use `p.Name == name`, and SQL Server's **case-insensitive collation** does the ignore-case part (Topic 8).

### 6.2 Async for real
Topic 4's `Task.Delay` simulation is gone. `ToListAsync` and `SaveChangesAsync` do **real network I/O** to SQL Server. While a request waits for the database, its thread goes back to the pool and serves other requests. The `CancellationToken` goes all the way to the database: if the client disconnects, the query is cancelled.

### 6.3 Include: loading related data
`Include(p => p.Tasks)` = "also load each project's tasks" → a **LEFT JOIN** (Topic 9). Without it, `project.Tasks` stays **empty** and the task counts would be 0. `Include(p => p.Tasks.OrderBy(t => t.Id))` also **orders** the included tasks (no ORDER BY = no order, Topic 8).
> ⚠️ `GetAllAsync` loads **every task of every project** just to count them. Fine for 7 tasks, wasteful for 100,000. Topic 11 replaces it with a **projection** (`Select(p => new { ..., TaskCount = p.Tasks.Count() })`), which becomes a `COUNT` in SQL.

### 6.4 Change tracking: Add, modify, Remove, SaveChanges
| Code | Tracker state | SQL sent at `SaveChangesAsync` |
|---|---|---|
| `db.Projects.Add(project)` | **Added** | `INSERT ... OUTPUT INSERTED.[Id]` → EF writes the new id into `project.Id` |
| load, then `project.Name = "x"` | **Modified** (EF compared with the original values) | `UPDATE ... SET [Description] = @p0, [Name] = @p1 WHERE [Id] = @p2` (only changed columns) |
| `db.Projects.Remove(project)` | **Deleted** | `DELETE FROM [Projects] WHERE [Id] = @p0` (the DB cascades to tasks) |
| after a successful save | **Unchanged** | nothing |

- **No `Update()` call is needed** in `UpdateAsync`: the entity was loaded by this DbContext, so it's tracked, and EF detects the changes itself.
- **`project.Id` is 0 until `SaveChangesAsync`**. Then it's the value SQL Server generated (Topic 8's Q8 `OUTPUT INSERTED.Id`, done for you). The DEBUG lab shows it.
- **One `SaveChangesAsync` = one transaction** (Topic 9): all the changes, or none.

### 6.5 The name rule: the check AND the index
```csharp
await EnsureNameIsFreeAsync(trimmedName, ...);   // SELECT CASE WHEN EXISTS (... WHERE [Name] = @name) ...
db.Projects.Add(project);
await SaveChangesAsync(trimmedName, ...);        // INSERT; the UNIQUE index may still say no
```
The check and the INSERT are **two round trips**. Two requests (maybe on two servers) can both pass the check. **That is Topic 4's race, now across servers.** The `lock` is gone (it only ever protected one process). The **UNIQUE index** catches the second INSERT with **error 2601**, and we translate it:
```csharp
catch (DbUpdateException ex) when (ex.InnerException is SqlException { Number: 2601 or 2627 })
{
    throw new ConflictException($"A project named '{projectName}' already exists.");
}
```
- **`when (...)` is an exception filter**: catch only if the condition is true; otherwise the exception flies on untouched. TS has no equivalent (you'd `catch`, check, and re-`throw`).
- **`is SqlException { Number: 2601 or 2627 }`** is a **property pattern** (Topic 1-style pattern matching): "is it a SqlException whose Number is 2601 or 2627?"
- **Why keep the check at all?** It gives the normal case a clean 409 without an exception from the database, and the index is the safety net for the rare race. Real run: of 30 concurrent requests, **10 passed the check and were stopped only by the index** (Part C, 12.2).

### 6.6 What happened to the `lock`?
Gone, and with it `_nextProjectId++`. The **database** generates ids (IDENTITY) and handles concurrent writers (transactions, locks, the UNIQUE index). Each request has **its own** DbContext and `ProjectService`, so there's no shared C# state left to protect.

## 7. The SQL EF Core generates (real, from our log)

`appsettings.Development.json` sets `"Microsoft.EntityFrameworkCore.Database.Command": "Information"`, so every SQL statement is logged in Rider's Run window. `EnableSensitiveDataLogging()` (Development only) also shows the parameter **values**. Never use it in production: it would log user data.

| C# | SQL (abridged) | Notes |
|---|---|---|
| `db.Projects.Include(p => p.Tasks).OrderBy(p => p.Id).ToListAsync()` | `SELECT [p].*, [t].* FROM [Projects] AS [p] LEFT JOIN [Tasks] AS [t] ON [p].[Id] = [t].[ProjectId] ORDER BY [p].[Id]` | **LEFT** join: Internal tools (no tasks) is kept (Topic 9) |
| `...SingleOrDefaultAsync(p => p.Id == id)` | `SELECT TOP(2) ... WHERE [p].[Id] = @id` | **TOP(2)**: `Single` must throw if there are 2 matches, so it asks for 2 to find out |
| `db.Projects.AnyAsync(p => p.Name == name)` | `SELECT CASE WHEN EXISTS (SELECT 1 FROM [Projects] AS [p] WHERE [p].[Name] = @name) THEN CAST(1 AS bit) ...` | `Any()` = **EXISTS** (Topic 9) |
| `p.Id != exceptProjectId` with `exceptProjectId = null` | (disappears from the SQL) | EF saw the parameter was null and simplified the condition. With `4`: `WHERE [p].[Id] <> @exceptProjectId` |
| `Add` + `SaveChangesAsync` | `INSERT INTO [Projects] (...) OUTPUT INSERTED.[Id] VALUES (@p0, @p1, @p2)` | Topic 8's Q8. Values are **parameters** (no injection) |
| modify + `SaveChangesAsync` | `UPDATE [Projects] SET [Description] = @p0, [Name] = @p1 OUTPUT 1 WHERE [Id] = @p2` | only the changed columns |
| `FindAsync([id])` | `SELECT TOP(1) ... WHERE [p].[Id] = @p` | by primary key |
| `Remove` + `SaveChangesAsync` | `DELETE FROM [Projects] OUTPUT 1 WHERE [Id] = @p0` | tasks: ON DELETE CASCADE |

You can now **read** every query EF sends. That's the point of Topics 8–9.

## 8. Dates: the UTC converter

SQL Server's `DATETIME2` stores a date and time but **not** whether it's UTC. EF reads it back with `Kind = Unspecified`, and JSON then prints `"2026-09-01T09:00:00"` **without the `Z`**, so the client can't tell it's UTC. `UtcDateTimeConverter` marks every `DateTime` read from the database as UTC (and converts local times to UTC on the way in). It's registered for **all** `DateTime`/`DateTime?` properties in `ConfigureConventions`. Real output: `"createdAt":"2026-09-01T09:00:00Z"`. Alternative used by many teams: `DateTimeOffset` + `datetimeoffset` columns, which store the offset too.

## 9. Smaller changes worth knowing
- **`InMemoryProjectService`**: the old service, renamed. Playground demos 03/04 and Debug Lab A still use it (they need no database). Both services implement `IProjectService`, and Program.cs picks one: **one line**.
- **`ProjectRules`**: `MaxNameLength` (100), `MaxDescriptionLength` (1000) and `MaxTitleLength` (200) are used by the C# validation **and** by `HasMaxLength(...)`, so the check and the column can never disagree. New: a too-long description is a **400** now. Without it, SQL Server would reject it (error 2628, "String or binary data would be truncated") → 500.
- **`DueDate`**: optional on `POST .../tasks`, returned in `TaskResponse`.
- **Security pin:** `Microsoft.Data.SqlClient` (used by EF Core) depends on `System.Security.Cryptography.Pkcs` **9.0.11**, which has known vulnerabilities (NuGet audit warnings NU1902/NU1903 at build time). The csproj references the patched **10.0.13** directly, and NuGet picks the higher version. 10.0.12 was still flagged, and 10.0.13 builds clean. **Lesson: build warnings about vulnerable packages are real work, not noise.**

---

# Part B: Run it locally

1. **SQL Server running:** `docker compose up -d` (Docker Desktop open). Pull the branch in Rider.
2. **Install the EF tool** (once per clone), in the repo root:
   ```bash
   dotnet tool restore
   ```
   It reads `dotnet-tools.json` and installs `dotnet-ef` 10.0.12 for this repo. Check: `dotnet ef --version`.
3. **Create the database from the migration:**
   ```bash
   dotnet ef database update --project src/ProjectHub.Api
   ```
   Expected: `Applying migration '20261017175147_InitialCreate'.` and `Done.`
   *It builds the project, reads the connection string from `appsettings.Development.json`, creates the database `ProjectHub`, runs the migration in a transaction, and records it in `__EFMigrationsHistory`.*
4. **DBeaver:** right-click the connection → Refresh. New database **`ProjectHub`**: tables `Projects`, `Tasks`, `__EFMigrationsHistory` (1 row). Open `Tasks` → **Constraints** and **Foreign Keys**: compare them with your hand-made `ProjectHubDb`.
5. **Run the API in Rider** (http profile). In the **Run** window, every request now prints the SQL it sent (`Executed DbCommand ...`).
6. **`ProjectHub.Api.http`:** run the requests **from "create a project" down to "delete it again", in order**. The create request saves the new id in `{{projectId}}`. The 409 still works: the name check now happens **in SQL**.
7. **The checkpoint: persistence.** Create a project, **stop the API**, start it again, `GET /api/projects` → it's still there. (Before Topic 10, a restart reset everything to `SampleData`.)
8. Optional: `dotnet ef migrations script --project src/ProjectHub.Api` prints the full SQL of the migration.

**Reset everything** (back to the seed data): `dotnet ef database drop --force --project src/ProjectHub.Api`, then step 3 again.

---

# Part C: The real results

## 12.1 The API against SQL Server (two runs, with a restart between them)
| Request | Result |
|---|---|
| `GET /api/projects` | 200: 3 seed projects, `taskCount` 4 / 3 / 0, dates with `Z` |
| `GET /api/projects/1` | 200: 4 tasks, ordered by id, each with `dueDate` |
| `POST` "Docs portal" | **201**, `Location: /api/projects/4`, `id` 4 (filled after the INSERT) |
| `POST` "WEBSITE REDESIGN" | **409** (the EXISTS check, case-insensitive collation) |
| `PUT /4` → "Docs portal v2" | 200 (UPDATE of 2 columns) |
| `PUT /4` → "Mobile app" | **409** |
| `POST /4/tasks` with `dueDate` | 201, task **id 8** |
| `POST /999/tasks` | 404 |
| `POST` with a 1001-character description | **400** (new rule) |
| **restart the API**, `GET /4` | 200: **still there**, with its task → **persistence** ✅ |
| `DELETE /4`, then again | 204, then 404 (its task was deleted by **cascade**) |
| `POST` "Docs portal" again | 201 with **id 5**, not 4: deleted ids are never reused (Topic 8) |

## 12.2 The race: 30 concurrent requests
3 rounds × 10 simultaneous `POST`s with the same new name:
```
round 2:   1 × 201   9 × 409
round 3:   1 × 201   9 × 409
log: 30 × EXISTS check, 12 × INSERT attempted, 2 succeeded,
     10 × "Cannot insert duplicate key row ... unique index 'IX_Projects_Name'" (Error Number 2601) → 409
```
**10 requests passed the C# check** and were stopped **only** by the UNIQUE index. Without it: 10 duplicate projects. The ids jumped from 9 to 19, because failed INSERTs use up identity values (Topic 8).

## 12.3 Captive dependency
`AddSingleton<IProjectService, ProjectService>()` → the app **refuses to start**:
```
Cannot consume scoped service 'ProjectHub.Api.Data.ProjectHubDbContext' from singleton 'ProjectHub.Api.Services.IProjectService'.
```

## 12.4 Forgot the migration / wrong database
The API **starts fine** either way. The first request fails:

| Situation | Result |
|---|---|
| empty database (migration not applied) | 500, `Invalid object name 'Projects'.` (**208**) |
| database doesn't exist | 500, `Cannot open database "ProjectHubMissing" requested by the login.` (**4060**) |

## 12.5 A query EF can't translate
`string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase)` inside `AnyAsync` → 500:
```
InvalidOperationException: The LINQ expression '... string.Equals(a: p.Name, b: @name, comparisonType: OrdinalIgnoreCase)'
could not be translated. Additional information: Translation of the 'string.Equals' overload with a
'StringComparison' parameter is not supported.
```

---

# Part D: Practice

## 13. DEBUG (in Rider, locally)
1. **Watch the id appear.** Breakpoint on `await SaveChangesAsync(trimmedName, cancellationToken);` in `ProjectService.CreateAsync`. Send the "create a project" request.
   - Before: hover `project.Id` → **0**. In **Evaluate Expression** (⌥F8): `db.ChangeTracker.DebugView.LongView` → the project with state **Added**.
   - **Step Over** (F8). Now `project.Id` = the database's value, and the same DebugView says **Unchanged**.
   - Look at the Run window: the `INSERT ... OUTPUT INSERTED.[Id]` was logged exactly at that step.
2. **Change tracking in UpdateAsync.** Breakpoint after `project.Name = trimmedName;`. Evaluate `db.ChangeTracker.DebugView.LongView`: `Name` is shown as **Modified**, with the original value. Step over the save and find the `UPDATE` in the log. Which columns does it set?
3. **Forget the migration.** Stop the API. `dotnet ef database drop --force --project src/ProjectHub.Api`. Start the API → it starts! Send `GET /api/projects` → 500. Find the **SqlException** and its number in the Run window. Fix it with `dotnet ef database update`, then try again. (Expected: 4060, "Cannot open database".)
4. **Captive dependency.** In `Program.cs`, change `AddScoped<IProjectService, ProjectService>` to `AddSingleton<...>`. Start → read the error → **undo**.
5. **Translation error.** In `EnsureNameIsFreeAsync`, replace `p.Name == name` with `string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase)`. Create a project → 500. Read the message → **undo**. Why does the same code work in `InMemoryProjectService`?

## 14. CHECK: answer these in your own words
1. What is EF Core? What are the provider, the DbContext and a DbSet?
2. Why is the DbContext Scoped? Why must `ProjectService` be Scoped now?
3. What is a migration? What do `migrations add` and `database update` do? What is `__EFMigrationsHistory` for?
4. Name three things EF Core decided **by convention** in our schema, and two we had to **configure**.
5. When is the SQL sent: at `db.Projects.Where(...)` or at `ToListAsync()`? `IEnumerable` vs `IQueryable`?
6. In `UpdateAsync`, why is there no `db.Update(project)` call? What does `SaveChangesAsync` send?
7. Where does `project.Id` come from after `CreateAsync`? What is it before `SaveChangesAsync`?
8. The service checks the name **and** catches error 2601. Why both?
9. Why does `SingleOrDefaultAsync` generate `TOP(2)`?
10. Why can't the query use `string.Equals(..., OrdinalIgnoreCase)`, and how is the name check still case-insensitive?
