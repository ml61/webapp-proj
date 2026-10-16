# Lesson 8: SQL basics: tables, keys, and the ten queries

**Roadmap:** Week 2, Topic 8. **Time:** about 2–3 h (the first-time setup takes longest).
**Checkpoint:** you can **query and change data without EF Core**.

**Files for this lesson** (in Rider: the new `sql` solution folder):
- `sql/01-create-database.sql`: creates the database `ProjectHubDb`
- `sql/02-create-tables.sql`: creates the `Projects` and `Tasks` tables, with keys and rules
- `sql/03-seed-data.sql`: fills them with the same data as `SampleData.cs`
- `sql/04-queries.sql`: **the ten queries**
- `sql/05-constraints.sql`: **break it**: six statements the database rejects on purpose

All five scripts were run against SQL Server 2025 in the cloud container. Section 7 has the real output.

**Why this topic exists:** in Topic 10, EF Core will write SQL *for* you. If you can't read SQL, EF is a black box: you can't check what it does, why it's slow, or what went wrong. Today you write it by hand.

---

# Part A: Concepts

## 1. A relational database in frontend terms

| Database | Closest JS/TS idea | ProjectHub |
|---|---|---|
| **database** | the whole app's data | `ProjectHubDb` |
| **table** | an array of objects that all have **exactly** the same shape | `Projects`, `Tasks` |
| **row** | one object in that array | the project "Website redesign" |
| **column** | a property, with a **fixed type** | `Name`, `CreatedAt` |
| **schema** (`dbo`) | a namespace/folder for tables | `dbo.Projects` ("database owner", the default) |

The big difference from a JS array: the database **enforces the shape and the rules** (types, required values, uniqueness, relationships) for *everyone* who writes to it, not just for your code.

Our C# entities map to tables directly:

| C# (`Entities/`) | SQL |
|---|---|
| class `Project` | table `dbo.Projects` |
| one `Project` object | one row |
| property `Name` (`string`, required) | column `Name NVARCHAR(100) NOT NULL` |
| property `Description` (`string?`) | column `Description NVARCHAR(1000) NULL` |
| `List<TaskItem> Tasks` | **no column!** Instead, each row in `Tasks` stores a `ProjectId` (section 3) |

## 2. Column types: C# → SQL Server

| C# | SQL Server | Note |
|---|---|---|
| `int` | `INT` | |
| `long` | `BIGINT` | |
| `string` | `NVARCHAR(n)` | **N** = Unicode (any language, emoji). `VARCHAR` without N is for non-Unicode text only. `n` = max length |
| `string` (no limit) | `NVARCHAR(MAX)` | for long text. Prefer a real limit |
| `DateTime` | `DATETIME2` | more precise than the old `DATETIME` |
| `bool` | `BIT` | 0 / 1 |
| `decimal` | `DECIMAL(18, 2)` | exact numbers: money (Topic 1) |
| `Guid` | `UNIQUEIDENTIFIER` | |
| `enum` | `INT` | `TaskItemStatus.Done` is stored as `2` (that's EF Core's default too) |
| `string?` / `int?` | the same type + **`NULL`** | the column allows "no value" |

## 3. Keys: how rows are identified and connected

**Primary key (PK):** the column that identifies each row: unique, never NULL. It's the entity identity from Topic 1 ("task 5 stays task 5 even after a rename").
```sql
Id INT IDENTITY(1, 1) NOT NULL,
CONSTRAINT PK_Projects PRIMARY KEY (Id)
```
**`IDENTITY(1, 1)`** = "the **database** generates the id: start at 1, add 1". That replaces our C# `_nextProjectId++` and the `lock` around it (Topic 4). The database does this safely, even with many servers inserting at once.

**Foreign key (FK):** a column that **points to the primary key of another table**. That's how a relationship is stored:
```sql
ProjectId INT NOT NULL,
CONSTRAINT FK_Tasks_Projects_ProjectId FOREIGN KEY (ProjectId) REFERENCES dbo.Projects (Id)
```
- **One-to-many:** one project has many tasks. The FK lives on the **"many" side** (`Tasks.ProjectId`). The `Projects` table has **no** list of tasks. "The tasks of project 1" = "rows in `Tasks` where `ProjectId = 1`". In C#, `project.Tasks` is a convenience. In the database, the relationship is just this number.
- The database **guarantees** that every `ProjectId` points to a project that exists, and it **refuses** to delete a project that still has tasks (section 6, C5). Alternative: `ON DELETE CASCADE` deletes the tasks automatically (EF Core uses cascade by default for required relationships, Topic 10).

```
Projects                          Tasks
┌────┬──────────────────┐         ┌────┬───────────┬────────────────────┬────────┐
│ Id │ Name             │         │ Id │ ProjectId │ Title              │ Status │
├────┼──────────────────┤         ├────┼───────────┼────────────────────┼────────┤
│ 1  │ Website redesign │◄────────┤ 1  │ 1         │ Design mockups     │ 2      │
│ 2  │ Mobile app       │◄──┐     │ 2  │ 1         │ Build landing page │ 1      │
│ 3  │ Internal tools   │   └─────┤ 5  │ 2         │ Login screen       │ 1      │
└────┴──────────────────┘         └────┴───────────┴────────────────────┴────────┘
```

## 4. Constraints: rules the database enforces

| Constraint | Our example | What it stops |
|---|---|---|
| `NOT NULL` | `Name NVARCHAR(100) NOT NULL` | missing required values |
| `PRIMARY KEY` | `PK_Projects` | duplicate or empty ids |
| `FOREIGN KEY` | `FK_Tasks_Projects_ProjectId` | tasks pointing to nothing; deleting a project that has tasks |
| `UNIQUE` | `UQ_Projects_Name` | **two projects with the same name**: our Topic 3 business rule |
| `CHECK` | `CK_Tasks_Status CHECK (Status IN (0, 1, 2))` | invalid status numbers |
| `DEFAULT` | `DF_Projects_CreatedAt DEFAULT SYSUTCDATETIME()` | nothing; it **fills** a value when none is given (like `= DateTime.UtcNow`) |

The prefixes `PK_`, `FK_`, `UQ_`, `CK_`, `DF_`, `IX_` are naming conventions. When an error says `UQ_Projects_Name`, you instantly know what kind of rule was broken, and where.

**Case-insensitive uniqueness for free:** SQL Server's default **collation** (the rules for comparing text) is case-**in**sensitive, so `UNIQUE (Name)` treats `Mobile app` and `MOBILE APP` as the same. That's exactly our `StringComparison.OrdinalIgnoreCase` rule (C1 proves it).

**"But C# already validates. Why rules in the database too?"**
1. **Other paths in.** Imports, other apps, a colleague's manual SQL. Topic 5's task #158 came from "the old tracker" and skipped our service's validation.
2. **Concurrency across servers.** Topic 4's `lock` only protects inside **one process**. With 3 servers behind a load balancer, two can insert "Mobile app" at the same moment. The **UNIQUE constraint** stops the second one, whichever server it came from. (Topic 4 promised this.)
3. **The last line of defense.** Data lives for years; code changes every week.

**Index** (`IX_Tasks_ProjectId`): a sorted lookup structure, like a book's index, that makes `WHERE ProjectId = 1` fast without scanning every row. Primary keys and unique constraints get one automatically. We add one on the FK because "the tasks of a project" is a common query. Topic 18 goes deeper.

## 5. Reading a query

```sql
SELECT Id, Title, Status        -- 3. which columns to return (like .Select)
FROM dbo.Tasks                  -- 1. which table
WHERE ProjectId = 1             -- 2. which rows (like .Where)
  AND Status <> 2
ORDER BY CreatedAt DESC;        -- 4. in which order (like .OrderByDescending)
```
- **Written order ≠ execution order.** The database logically does **FROM → WHERE → SELECT → ORDER BY**. LINQ's method chain (`tasks.Where(...).Select(...)`) is actually closer to how SQL *runs*.
- **Declarative:** you say **what** you want, not **how** to get it (no loops). The database picks the strategy (use an index or scan the table). Topic 18 shows how to look at its plan.
- Syntax differences from C#: `=` (not `==`), `<>` (not `!=`), `AND` / `OR` / `NOT`, strings in **single quotes** with `N` for Unicode: `N'Mobile app'`. Comments start with `--`.
- `GO` (in our scripts) isn't SQL. It's an instruction to the **tool** (sqlcmd, DBeaver, SSMS): "send everything above as one batch". Some statements, like `CREATE DATABASE` followed by `USE`, need to be in separate batches.

### NULL: the most common SQL trap
`NULL` means **"unknown / no value"**. It's not `""` and not `0`. Any comparison with NULL is **unknown**, which is neither true nor false, so `WHERE Description = NULL` matches **nothing**. Use **`IS NULL`** / **`IS NOT NULL`**. In the real run, Q7 found "Mobile app" and Q7b found 0 rows.

### No ORDER BY = no order
A table is a **set**, not an array. Without `ORDER BY`, the database returns rows in whatever order is cheapest for it. In our run, the last `SELECT` came back as **3, 2, 1** (it happened to use the name index). Your UI shows a list? **Always `ORDER BY`.**

### UPDATE and DELETE: the WHERE is everything
```sql
UPDATE dbo.Projects SET Name = N'x';           -- ⚠️ no WHERE: EVERY project is renamed
DELETE FROM dbo.Tasks;                          -- ⚠️ no WHERE: EVERY task is gone
```
There's no undo. Habit: **run a `SELECT` with the same `WHERE` first**, check the rows, *then* turn it into the `UPDATE`/`DELETE`. That's what Q9 does. Topic 9 adds **transactions** (`BEGIN TRAN` … `ROLLBACK`), a real safety net.

### Security preview: never glue user input into SQL
```csharp
var sql = "SELECT * FROM Projects WHERE Name = '" + userInput + "'";   // ❌ SQL injection
```
If `userInput` is `x'; DROP TABLE Projects; --`, the database runs **your query plus theirs**. The fix is **parameters**: the SQL text and the values travel **separately** (`WHERE Name = @name`). EF Core (Topic 10) always sends parameters, which you'll see in the generated SQL as `@p0`.

---

# Part B: Setup, step by step (first time with Docker and DBeaver)

## 6. Start SQL Server with Docker

**What Docker is, in one sentence:** it runs a program (here, SQL Server, which is a Linux program) in an isolated "container" on your Mac, so you don't have to install it. `docker-compose.yml` in the repo describes exactly which container to run.

1. **Open Docker Desktop** (Applications → Docker). Wait until it shows **"Engine running"** (bottom-left in the window, and the whale icon in the menu bar stops animating). The first start can take a minute.
2. **If your Mac has an Apple chip (M1/M2/M3/M4):** SQL Server only exists for Intel (`amd64`), so Docker must emulate it. In Docker Desktop → **Settings** (gear icon) → **General** → make sure **"Use Rosetta for x86_64/amd64 emulation on Apple Silicon"** is **on** → Apply & restart. (Our `docker-compose.yml` already says `platform: linux/amd64`.) To check your chip: Apple menu → About This Mac.
3. **Open a terminal in the repo root.** In Rider: the **Terminal** tab. Then run:
   ```bash
   docker compose up -d
   ```
   - `up` = create and start the container. `-d` = in the background ("detached"), so the terminal stays free.
   - **The first time it downloads the SQL Server image (about 600 MB to 2.4 GB on disk)**, which takes a few minutes. Later starts take seconds.
4. **Check it's running:**
   ```bash
   docker ps
   ```
   You should see a line with `projecthub-sql` and a status like `Up 30 seconds`. The container is also visible in Docker Desktop → **Containers**.
5. **Wait until SQL Server is ready** (about 20–60 s after starting, longer under Rosetta):
   ```bash
   docker logs projecthub-sql
   ```
   Look for the line **`SQL Server is now ready for client connections`**. If it's not there yet, wait and run it again.

**Daily commands** (run in the repo root):
| Command | What it does |
|---|---|
| `docker compose up -d` | start SQL Server |
| `docker compose stop` | stop it (data is kept) |
| `docker compose down` | remove the container (data is **kept**, in the `sqldata` volume) |
| `docker compose down -v` | remove everything **including the data** (a fresh start) |

**Connection details** (from `docker-compose.yml`, development only):

| Setting | Value |
|---|---|
| Host | `localhost` |
| Port | `1433` |
| User | `sa` (the built-in admin, "system administrator") |
| Password | `ProjectHub_Dev123!` |

## 7. Connect with DBeaver

**DBeaver** is a database client: it shows tables, runs SQL, and edits data, a bit like a database IDE. Menu names below are for current DBeaver Community versions. If something looks different, send me a screenshot.

1. **Open DBeaver.** If it asks to create a sample database, say **No**.
2. **New connection:** menu **Database → New Database Connection** (or the plug icon with a **+**, top-left).
3. Choose **SQL Server** (type "sql server" in the search box) → **Next**.
4. **Main** tab:
   - **Host:** `localhost`  **Port:** `1433`
   - **Database/Schema:** `master` (the server's built-in system database. Our database doesn't exist yet.)
   - **Authentication:** `SQL Server Authentication`
   - **Username:** `sa`  **Password:** `ProjectHub_Dev123!`  and tick **Save password**
   - If you see a **"Trust Server Certificate"** checkbox, **tick it** (see step 6).
5. Click **Test Connection…**
   - **First time:** DBeaver says the **driver files are missing** and offers to download them → **Download**. (The driver is the library DBeaver uses to talk to SQL Server.)
   - Expected: **"Connected"**.
6. **If you get a certificate / SSL / "PKIX path building failed" error:** SQL Server encrypts connections with a self-signed certificate, which DBeaver doesn't trust by default. Fix: in the connection settings, open the **Driver properties** tab, find **`trustServerCertificate`**, set it to **`true`**, then Test Connection again. (Local development only. A real server needs a real certificate.)
7. Click **Finish**. The connection appears on the left, in the **Database Navigator**.

**If Test Connection fails:**
| Symptom | Cause | Fix |
|---|---|---|
| "Connection refused" / timeout | the container isn't running, or SQL Server isn't ready yet | `docker ps`, then `docker logs projecthub-sql` (wait for "ready") |
| "Login failed for user 'sa'" | wrong password | copy it exactly: `ProjectHub_Dev123!` |
| certificate / SSL error | self-signed certificate | `trustServerCertificate = true` (step 6) |

## 8. Run the scripts in DBeaver

1. **Open a script:** menu **File → Open File…** → choose `sql/01-create-database.sql` in the repo.
   **Link it to your connection** (otherwise running it says *"No active connection"*). The tab title shows `<none> 01-create-database.sql` while it isn't linked:
   click inside the editor → menu **SQL Editor → Set active connection** (usually **⌘9**; or **⌘3** *Find Actions* → type `active connection`) → pick **master localhost:1433**.
   The tab title changes to `<master> ...`. Do this once per file; DBeaver remembers it. `<master>` is fine: every script starts with `USE ProjectHubDb;`.
2. **Two ways to run:**
   - **Execute SQL Script** (the **second** ▶ on the editor's left edge, the one with a small **+**; usually **⌥X** / Option+X): runs the **whole file**, top to bottom. **Use this for 01, 02 and 03.** (With the other button, only the statement under the cursor runs, and script 01 seems to "do nothing".)
   - **Execute SQL Statement** (▶ icon, usually **⌘↩** / Cmd+Enter): runs only the **statement under the cursor**. That's the one for `04` and `05`, one query at a time.
   - Results appear in the **bottom panel**, one tab per result.
3. **Run in this order:**
   1. `01-create-database.sql`: **whole script**. Result: one row, `ProjectHubDb`.
   2. `02-create-tables.sql`: **whole script**. Result: `Projects`, `Tasks`.
   3. `03-seed-data.sql`: **whole script**. Result: 3 projects, 7 tasks.
   4. `04-queries.sql`: **one statement at a time** (cursor in the query → Cmd+Enter). Read each result and compare it with section 9.
   5. `05-constraints.sql`: **one statement at a time**. Each one **fails on purpose**. Read the error.
4. **See the new database in the navigator:** right-click the connection → **Refresh** (F5). Then expand **Databases → ProjectHubDb → Schemas → dbo → Tables**.
5. **Look around:**
   - double-click the **Projects** table → **Data** tab: the rows, like a spreadsheet
   - **Properties / Columns / Constraints** tabs: the types and rules you created
   - open the **Tasks** table → **ER Diagram** tab: the FK line from `Tasks` to `Projects`, drawn for you

The scripts start with `USE ProjectHubDb;`, so they work even while your connection points at `master`.

**Alternative without DBeaver** (command line, the same tool I used in the cloud):
```bash
docker exec -it projecthub-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'ProjectHub_Dev123!' -C
```
Then type SQL, ending each batch with `GO`. Quit with `exit`. (`-C` = trust the self-signed certificate.)

---

# Part C: The scripts and the real results

## 9. The ten queries (`04-queries.sql`)

| # | Query | LINQ / API equivalent | Real result |
|---|---|---|---|
| Q1 | `SELECT * FROM dbo.Projects` | `GET /api/projects` | 3 rows |
| Q2 | `SELECT Id, Name, Description ... WHERE Id = 1` | `GET /api/projects/1`, `FirstOrDefault(p => p.Id == 1)` | Website redesign |
| Q3 | `WHERE ProjectId = 1 AND Status <> 2` | `Where(t => t.ProjectId == 1 && t.Status != Done)` | 2: Build landing page, SEO audit |
| Q4 | `ORDER BY CreatedAt DESC, Title ASC` | `OrderByDescending(...).ThenBy(...)` | 7 rows, App store listing first |
| Q5 | `ORDER BY Id OFFSET 3 ROWS FETCH NEXT 3 ROWS ONLY` | `Skip(3).Take(3)` | tasks 4, 5, 6 |
| Q6 | `WHERE Name LIKE N'%app%'` | `Where(p => p.Name.Contains("app"))` | Mobile app |
| Q7 | `WHERE Description IS NULL` | `Where(p => p.Description == null)` | Mobile app |
| Q7b | `WHERE Description = NULL` | (a trap) | **0 rows** |
| Q8 | `INSERT ... OUTPUT INSERTED.Id, ... VALUES (N'Docs portal', ...)` | `POST /api/projects` → 201 + body | Id 4, CreatedAt filled by the DEFAULT |
| Q9 | `SELECT` first, then `UPDATE ... SET ... WHERE Name = N'Docs portal'` | `PUT /api/projects/4` | renamed to "Docs portal v2" |
| Q10 | `DELETE FROM dbo.Projects WHERE Name = N'Docs portal v2'` | `DELETE /api/projects/4` | back to 3 projects (order 3, 2, 1: no ORDER BY!) |

## 10. Break it (`05-constraints.sql`): what the database refuses

| # | Statement | Real error | In our API it would be… |
|---|---|---|---|
| C1 | `INSERT ... (N'MOBILE APP')` | **Msg 2627** Violation of UNIQUE KEY constraint `UQ_Projects_Name`. The duplicate key value is (MOBILE APP). | **409** Conflict |
| C2 | task with `ProjectId = 999` | **Msg 547** conflicted with the FOREIGN KEY constraint `FK_Tasks_Projects_ProjectId` | **404** Not Found |
| C3 | task with `Status = 7` | **Msg 547** conflicted with the CHECK constraint `CK_Tasks_Status` | **400** |
| C4 | project with `Name = NULL` | **Msg 515** Cannot insert the value NULL into column 'Name' | **400** (automatic validation, Topic 6) |
| C5 | `DELETE` project 1 (has tasks) | **Msg 547** The DELETE statement conflicted with the REFERENCE constraint `FK_Tasks_Projects_ProjectId` | **409** (or delete the tasks first / cascade) |
| C6 | a valid insert after the failures | gets **Id 7**, not 4 | ids are **not** consecutive |

How to read an error: **the number** (2627 = unique, 547 = FK or CHECK, 515 = NULL), **the constraint name** (that's why we named them), **the table/column**. "The statement has been terminated" means **nothing** was changed.

**C6, the identity gap:** Id 4 was used by "Docs portal" (and deleted ids are **never reused**), and the failed inserts also **used up** numbers. So the next project got 7. Never build logic on "ids are 1, 2, 3, …".

---

# Part D: Practice

## 11. DEBUG (no debugger for SQL, so you investigate with the tools)

1. **Read the errors.** Run each `05` statement and, for each, write down the error number, the constraint name, and which of our C# rules (Topic 3/6) it matches.
2. **NULL experiment:** run Q7 and Q7b. Then try `SELECT * FROM dbo.Projects WHERE Description <> N'x';`. Does "Mobile app" (NULL description) appear? Why not?
3. **Order experiment:** run `SELECT Id, Name FROM dbo.Projects;` several times, then `... ORDER BY Id;`. Which one would you trust in a UI?
4. **ER diagram:** in DBeaver, open the `Tasks` table → **ER Diagram**. Find the FK line. Which side is the "many" side?
5. **Make your own query:** "all Todo tasks of the Mobile app project, oldest first". (Use `ProjectId = 2`. Topic 9 shows how to use the project *name* with a JOIN.) Send it to me.

## 12. CHECK: answer these in your own words

1. Table, row, column, primary key, foreign key: explain each with a ProjectHub example.
2. Why does `Projects` have no "tasks" column? Where does the relationship live?
3. What does `IDENTITY(1, 1)` do, and which C# code (Topic 4) does it replace?
4. Why put a UNIQUE constraint on `Name` when `ProjectService` already checks for duplicates? Give two reasons.
5. `NVARCHAR(100)` vs `VARCHAR(100)`: what's the difference?
6. Why does `WHERE Description = NULL` return nothing? What do you write instead?
7. Why must a UI query have `ORDER BY`?
8. What's dangerous about `UPDATE` and `DELETE`, and what's your safety habit?
9. Map these errors to HTTP status codes: 2627, 547 on INSERT (FK), 515.
10. What is SQL injection, and what prevents it?
