# Lesson 9: JOINs, GROUP BY, subqueries, transactions

**Roadmap:** Week 2, Topic 9. **Time:** about 2–3 h.
**Build:** the two reports, **overdue tasks** and **tasks per project**, plus `BEGIN TRAN` + `ROLLBACK`.
**Checkpoint:** explain **why a JOIN is needed** and **what a transaction protects**.

**Files for this lesson** (Rider: the `sql` solution folder):
- `sql/06-add-due-date.sql`: adds a `DueDate` column to `Tasks`, a **schema change on a table that already has data**
- `sql/07-joins.sql`: INNER and LEFT JOIN, the LEFT JOIN trap, **REPORT 1: overdue tasks**
- `sql/08-group-by.sql`: aggregates, GROUP BY, HAVING, the COUNT(*) trap, **REPORT 2: tasks per project**
- `sql/09-subqueries-exists.sql`: subqueries, IN, EXISTS / NOT EXISTS, the NOT IN trap
- `sql/10-transactions.sql`: BEGIN / COMMIT / ROLLBACK, the "error doesn't undo" trap, the correct pattern

All five were run against SQL Server 2025 in the cloud, twice (they're re-runnable). Part C has the real output.

**Why this topic exists:** Topic 8 queried **one table at a time**. Real questions span tables ("tasks **with their project name**"), summarize ("how many tasks **per** project"), and change several rows that must stay consistent ("delete a project **and** its tasks"). In Topic 10–11, EF Core generates all of this: `Include` becomes a JOIN, `GroupBy` becomes GROUP BY, `Any()` becomes EXISTS, and `SaveChanges` runs in a transaction. Today you learn what it generates.

---

# Part A: Concepts

## 1. Why a JOIN is needed

In Topic 8 we split the data on purpose: the project's name is stored **once**, in `Projects`. Each task stores only `ProjectId`. This is called **normalization**: each fact lives in one place, so renaming a project is one UPDATE, not one per task.

The price is that a question like "show tasks with their project name" needs **both tables**. A JOIN puts the rows back together through the foreign key:

```sql
SELECT t.Id, t.Title, p.Name AS ProjectName
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId;
```

**In TypeScript terms**, you'd do this in the frontend:
```ts
const projectsById = new Map(projects.map(p => [p.id, p]));
const rows = tasks.map(t => ({ ...t, projectName: projectsById.get(t.projectId)!.name }));
```
A JOIN is that `map` + lookup, done **inside the database**, in **one query**.

**The alternative, and why it's bad: N+1 queries.** Load the 7 tasks (1 query), then for each task load its project (7 more queries). That's 8 round trips instead of 1. With 1,000 tasks it's 1,001 round trips. Each one costs network time, so the page gets slow. This is the most famous ORM performance bug, and Topic 11 shows how EF Core can cause it.

> **Checkpoint answer, part 1:** data is split across tables to store each fact once (normalization). A JOIN combines the rows again **in one query**, matching the FK to the PK. Without it, you'd need N+1 queries or duplicated data.

- **`AS t` / `AS p` are aliases**, short names for the tables. Once two tables are involved, write `t.Title`, not `Title`. Both tables have `Id` and `CreatedAt`, so `Id` alone is ambiguous (that's an error).
- **`ON`** says how rows match: almost always **FK = PK**.

## 2. INNER JOIN vs LEFT JOIN

| | Keeps | Our data |
|---|---|---|
| **INNER JOIN** | only rows that have a match **on both sides** | 7 rows. "Internal tools" (no tasks) is **missing** |
| **LEFT JOIN** | **every** row of the **left** table (the one after `FROM`), matched where possible, otherwise **NULL** on the right side | 8 rows: "Internal tools" appears once, with `TaskId` and `Title` = NULL |

```
Projects LEFT JOIN Tasks:

 Website redesign ── Design mockups
 Website redesign ── Build landing page        INNER JOIN keeps only rows with a match
 Website redesign ── SEO audit                 on both sides: these 7.
 Website redesign ── Write copy
 Mobile app       ── Login screen
 Mobile app       ── Push notifications
 Mobile app       ── App store listing
 Internal tools   ── NULL                       <- only LEFT JOIN keeps this one
```

- **Which one?** Ask: "should a project with **zero** tasks still appear?" Yes → LEFT JOIN (reports, dashboards). No → INNER JOIN.
- `RIGHT JOIN` is a LEFT JOIN with the tables swapped (rarely used; write it as a LEFT JOIN). `FULL JOIN` keeps unmatched rows from both sides. `CROSS JOIN` pairs every row with every row. You'll rarely need them.
- **LINQ:** INNER = `Join(...)`. LEFT = `GroupJoin(...).SelectMany(..., DefaultIfEmpty())`, which is awkward. With EF Core you mostly write navigation properties (`t.Project.Name`) and EF writes the JOIN (Topic 11).

### The LEFT JOIN trap: ON vs WHERE
"Every project, with its **open** tasks":
```sql
-- WRONG: "Internal tools" disappears
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
WHERE t.Status <> 2

-- RIGHT: the condition decides WHICH TASKS match; every project stays
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id AND t.Status <> 2
```
**Why:** `WHERE` runs **after** the join. The "Internal tools" row has `t.Status = NULL`, and `NULL <> 2` is UNKNOWN (Topic 8), so WHERE throws the row away. The LEFT JOIN silently became an INNER JOIN. **Rule:** in a LEFT JOIN, conditions on the **right** table go in `ON`.

## 3. The full logical order of a query

```
FROM / JOIN  ->  WHERE  ->  GROUP BY  ->  HAVING  ->  SELECT  ->  ORDER BY  ->  OFFSET / FETCH
 which rows      filter     make         filter      compute     sort          page
 (combined)      rows       groups       groups      columns
```
Most rules in this lesson follow from this order:
- `WHERE COUNT(*) > 2` is an error: when WHERE runs, nothing has been counted yet. Use `HAVING`.
- A `SELECT` alias (`AS DaysOverdue`) can't be used in `WHERE` (SELECT runs later), but it can be used in `ORDER BY`.
- The LEFT JOIN trap: WHERE runs after the JOIN.

## 4. GROUP BY and aggregates

**Aggregates** turn many rows into one value: `COUNT`, `SUM`, `MIN`, `MAX`, `AVG`.

| SQL | LINQ |
|---|---|
| `SELECT COUNT(*) FROM dbo.Tasks` | `tasks.Count()` |
| `SELECT MAX(CreatedAt) FROM dbo.Tasks` | `tasks.Max(t => t.CreatedAt)` |
| `SELECT Status, COUNT(*) FROM dbo.Tasks GROUP BY Status` | `tasks.GroupBy(t => t.Status).Select(g => new { g.Key, Count = g.Count() })` |

**GROUP BY** = "one output row **per distinct value**". Like `Object.groupBy(tasks, t => t.status)` in JS, followed by a count per group.

**The rule:** every column in `SELECT` must either be **in `GROUP BY`** or **inside an aggregate**. `SELECT Status, Title, COUNT(*) ... GROUP BY Status` is an error. A group of 3 Todo tasks has 3 different titles, so which one should be shown? The database refuses to guess.

### COUNT(*) vs COUNT(column): the second trap
- `COUNT(*)` counts **rows**.
- `COUNT(column)` counts **non-NULL values** in that column.

They differ exactly where it hurts: with a LEFT JOIN, "Internal tools" has **one row** (with NULLs), so `COUNT(*)` says **1 task**. `COUNT(t.Id)` says **0**. Real output (G3):
```
Name             Tasks_WRONG Tasks_RIGHT
Internal tools   1           0
```
**Rule:** after a LEFT JOIN, count a column from the right table (`COUNT(t.Id)`), never `COUNT(*)`.

### HAVING = WHERE for groups
```sql
WHERE t.Status <> 2          -- filters ROWS, before grouping (drop Done tasks)
GROUP BY p.Id, p.Name
HAVING COUNT(*) > 2          -- filters GROUPS, after counting
```
LINQ: `.Where(...)` **before** `.GroupBy(...)` = WHERE. `.Where(g => g.Count() > 2)` **after** = HAVING.

### Conditional aggregation: several counts in one pass
```sql
SUM(CASE WHEN t.Status = 0 THEN 1 ELSE 0 END) AS Todo
```
`CASE WHEN ... THEN ... ELSE ... END` is SQL's ternary (`status === 0 ? 1 : 0`). Summing the 1s counts the Todo tasks. Do this once per status and you get a whole status breakdown per project in **one query**. That's **REPORT 2**.

## 5. Subqueries and EXISTS

A **subquery** is a query inside another query, in parentheses.

| Kind | Returns | Example (script 09) | LINQ |
|---|---|---|---|
| **scalar** | one value | `WHERE CreatedAt = (SELECT MAX(CreatedAt) FROM dbo.Tasks)` | `var max = tasks.Max(...); tasks.Where(t => t.CreatedAt == max)` |
| **IN** | a list | `WHERE Id IN (SELECT ProjectId FROM dbo.Tasks WHERE Status = 2)` | `ids.Contains(p.Id)` |
| **EXISTS** | true / false | `WHERE EXISTS (SELECT 1 FROM dbo.Tasks AS t WHERE t.ProjectId = p.Id AND ...)` | `tasks.Any(t => t.ProjectId == p.Id && ...)` |

**EXISTS** is SQL's `.some()` / `.Any()`: "is there **at least one** matching row?"
- The subquery uses `p.Id` from the **outer** query. That's a **correlated** subquery: it's checked once per project.
- `SELECT 1` is a convention: EXISTS ignores what's selected and only checks whether a row exists.
- The database can **stop at the first match**. It doesn't need to count them all.
- `NOT EXISTS` = "has **no** matching row" (projects without tasks). `LEFT JOIN ... WHERE t.Id IS NULL` gives the same result, and you'll see both styles.

### The NOT IN trap (the third NULL trap)
`x NOT IN (a, b, NULL)` means `x <> a AND x <> b AND x <> NULL`. The last part is UNKNOWN, so the whole condition is **never TRUE** → **0 rows**, silently. S5 shows it: project 2's due dates include task 6's NULL, so `NOT IN` returns nothing. **Rule:** use `NOT EXISTS` instead of `NOT IN (subquery)`, unless the column is `NOT NULL`.

## 6. Transactions

**A transaction groups several statements into one unit: all of them happen, or none do.**

Example: "delete project 1" is **two** statements, because the FK (Topic 8, C5) forces you to delete its tasks first:
```sql
DELETE FROM dbo.Tasks    WHERE ProjectId = 1;
DELETE FROM dbo.Projects WHERE Id = 1;
```
If the server crashes, the connection drops, or the second statement fails **between** them, the tasks are gone and the project remains. That's half an operation, and nothing will ever fix it.

```sql
BEGIN TRANSACTION;
    DELETE FROM dbo.Tasks    WHERE ProjectId = 1;
    DELETE FROM dbo.Projects WHERE Id = 1;
COMMIT TRANSACTION;     -- make it permanent      (or ROLLBACK TRANSACTION: undo everything since BEGIN)
```

**TS analogy:** it's like building a new state object and calling `setState` only at the end: the UI never sees a half-updated state. Or `Promise.all` with "if any part fails, nothing happened". (Promises don't actually give you that. Transactions do.)

### ACID: what a transaction protects (interview classic)
| Letter | Means | ProjectHub example |
|---|---|---|
| **A**tomicity | all or nothing | tasks and project are deleted together, or neither |
| **C**onsistency | the data moves from one valid state to another; constraints hold at the end | no task points to a deleted project |
| **I**solation | other sessions don't see your half-done work | another request doesn't see "tasks deleted, project still there" |
| **D**urability | once COMMIT returns, it survives a crash | written to the transaction log on disk |

> **Checkpoint answer, part 2:** a transaction protects a **multi-step change**. Atomicity: all steps or none. Isolation: nobody sees or overwrites the half-done state. In practice: no half-deleted projects, no money taken from one account but never added to the other.

### Autocommit: you've been using transactions all along
Without `BEGIN TRANSACTION`, SQL Server runs **each statement as its own transaction** (autocommit). That's why in Topic 8 a failed INSERT left nothing behind: "The statement has been terminated". You only need `BEGIN TRANSACTION` when **several** statements must stay together.

### The SQL Server trap: an error does NOT undo the transaction
By default, an error like 547 (CHECK) cancels **only the failing statement**. The transaction stays open, the earlier statements are still there, and a `COMMIT` would save half the work. T2 proves it: after the error, `XACT_STATE() = 1` ("still committable") and the half-created project still exists.

**The correct pattern** (T3), which you'll see in real stored procedures:
```sql
SET XACT_ABORT ON;                 -- any error dooms the WHOLE transaction
BEGIN TRY
    BEGIN TRANSACTION;
    -- ... several statements ...
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;                         -- re-raise, like C# "throw;" (Topic 3)
END CATCH;
```
- `@@TRANCOUNT` = number of open transactions in this session (0 = none).
- `XACT_STATE()`: 1 = open and committable, −1 = open but doomed (only ROLLBACK allowed), 0 = none.

**In C# (Topic 10):** EF Core's `SaveChangesAsync()` sends all pending changes **in one transaction** automatically. Everything is saved, or nothing is, and an exception is thrown. For several `SaveChanges` calls in one unit, there's `await using var tx = await db.Database.BeginTransactionAsync(); ... await tx.CommitAsync();`. If you don't commit, disposing the transaction rolls it back.

### Locks: the cost of isolation
While a transaction changes a row, it holds a **lock** on it until COMMIT/ROLLBACK. Another session that wants to **read** that row **waits** (SQL Server's default isolation level is **READ COMMITTED**: you never read uncommitted data). Real experiment from the cloud (two sessions):
```
session 77: BEGIN TRAN; UPDATE project 1 ...      (holds the lock for 10 s)
session 78: SELECT project 1   -> waits ... "Lock request time out period exceeded" (we set a 3 s limit)
session 78: SELECT project 2   -> answers immediately (only row 1 is locked)
who blocks whom:  session 78  blocked by 77  wait_type LCK_M_S
```
**Rules that follow:**
1. **Keep transactions short.** Never wait for a user, an HTTP call or a file inside one.
2. **Never leave one open.** A forgotten `BEGIN TRAN` in DBeaver blocks your own API (the DEBUG lab shows it). Check with `SELECT @@TRANCOUNT;`.

---

# Part B: Run it

**Before anything:** the DBeaver toolbar must say **`dbo@ProjectHubDb`** (Topic 8's lesson). If in doubt: `SELECT DB_NAME();`.

1. **Terminal** (repo root), once: the schema change.
   ```bash
   ./scripts/run-sql.sh sql/06-add-due-date.sql
   ```
   Expected: 7 × `(1 rows affected)` and a table of 7 tasks with a `DueDate` column (task 6: NULL). In DBeaver: right-click `Tasks` → **Refresh**, and the column appears.
   *Why the terminal:* it's a setup script (like 01–03). **Why it's interesting:** `ALTER TABLE ... ADD` changes a table that **already has data**. That's what an EF Core **migration** does (Topic 10). The new column is nullable, so existing rows simply get NULL. A `NOT NULL` column would need a `DEFAULT` for the existing rows.
2. **DBeaver**, `07`, `08`, `09`: one query at a time, like Topic 8: cursor in the query → top ▶. If DBeaver cuts a long query, **select it with the mouse first**.
3. **DBeaver**, `10`:
   - **T1 one statement at a time** (all in the same editor tab, which is the same connection and therefore the same transaction). Watch `@@TRANCOUNT` go 1 → 0. After the `DELETE`s, look at the projects **before** `ROLLBACK`: project 1 is gone. After the ROLLBACK, it's back.
   - **T2 and T3: select the whole block** (from `SET XACT_ABORT` to `END CATCH;`) with the mouse, then ▶. A TRY/CATCH block must be sent as **one** piece.
   - Or run the whole file in the terminal: `./scripts/run-sql.sh sql/10-transactions.sql`.
   - DBeaver might switch its toolbar from **Auto** to a transaction mode, or show a pending-transaction counter, after `BEGIN TRANSACTION`. That's DBeaver noticing the open transaction. Your `ROLLBACK` / `COMMIT` statements still work.
   - **Before closing the editor:** `SELECT @@TRANCOUNT;` must be **0**.

---

# Part C: The real results

## 7. JOINs (`07-joins.sql`)
| # | What | Result |
|---|---|---|
| J1 | INNER JOIN tasks + project names | 7 rows. **No** row for Internal tools |
| J2 | LEFT JOIN projects + tasks | 8 rows. `Internal tools  NULL  NULL` |
| J3a | LEFT JOIN + `WHERE t.Status <> 2` | 5 rows. **Internal tools is gone** (the trap) |
| J3b | LEFT JOIN + the condition in `ON` | 6 rows. Internal tools is kept, with NULLs |
| J4 | Todo tasks of "Mobile app" **by name** | 6 Push notifications, 7 App store listing |

**REPORT 1: overdue tasks** (run on 17 Oct 2026; `DaysOverdue` grows every day):
```
ProjectName       Id  Title               Status  DueDate     DaysOverdue
Mobile app        5   Login screen        1       2026-09-30  17
Website redesign  2   Build landing page  1       2026-10-01  16
Mobile app        7   App store listing   0       2026-10-10  7
```
Not in the report, and why: tasks 1 and 4 are past due but **Done**. Task 3 is due in 2027. Task 6 has **no due date** (`NULL < now` is UNKNOWN).

## 8. GROUP BY (`08-group-by.sql`)
| # | What | Result |
|---|---|---|
| G1 | COUNT(*), COUNT(DueDate), MIN, MAX | 7, **6** (one NULL), 09-02, 09-08 |
| G2 | tasks per status | 0 → 3, 1 → 2, 2 → 2 |
| G3 | COUNT(*) vs COUNT(t.Id) after LEFT JOIN | Internal tools: **1** vs **0** |
| G4 | HAVING: more than 2 open tasks | Mobile app 3 |

**REPORT 2: tasks per project:**
```
Id  Name              TotalTasks  Todo  InProgress  Done  Overdue
3   Internal tools    0           0     0           0     0
2   Mobile app        3           2     1           0     2
1   Website redesign  4           1     1           2     1
```

## 9. Subqueries and EXISTS (`09-subqueries-exists.sql`)
| # | What | Result |
|---|---|---|
| S1 | scalar: the newest task | 7 App store listing |
| S2 | IN: projects with a Done task | Website redesign |
| S3 | EXISTS: projects with open tasks | Website redesign, Mobile app |
| S4 | NOT EXISTS / LEFT JOIN IS NULL: projects without tasks | Internal tools (both versions) |
| S5 | **NOT IN with a NULL in the list** | **0 rows** (the trap) |
| S5b | the same with NOT EXISTS | tasks 1–4 |

## 10. Transactions (`10-transactions.sql`)
| Block | What happened |
|---|---|
| T1 | `@@TRANCOUNT` 1 → deleted 4 tasks + 1 project → only projects 2, 3 visible → **ROLLBACK** → projects 1, 2, 3 and 4 tasks back → `@@TRANCOUNT` 0 |
| T2 | error **547**, `XACT_STATE() = 1`, the half-created project **still exists** inside the open transaction → rolled back by hand |
| T3 | `XACT_ABORT ON`: error **547**, `XACT_STATE() = −1` (doomed) → ROLLBACK |
| check | `DemoProjects = 0`: nothing half-done was left behind |

Side effect you can spot: T2 and T3 used up identity values (Topic 8's gaps). A rollback does not give ids back.

---

# Part D: Practice

## 11. DEBUG (no debugger for SQL, so you investigate with the tools)

1. **The LEFT JOIN trap.** Run J3a and J3b. Explain in one sentence why Internal tools disappears in J3a.
2. **The COUNT trap.** Run G3. Why does `COUNT(*)` say 1 for a project with no tasks?
3. **Blocking lab (two editors).** This is how you investigate a "the API hangs" bug.
   - Open `07-joins.sql` in a **second** DBeaver editor tab. DBeaver gives each editor **its own connection** by default (each one is a separate session).
   - **Editor A:**
     ```sql
     BEGIN TRANSACTION;
     UPDATE dbo.Projects SET Name = N'Website redesign (editing)' WHERE Id = 1;
     ```
     Don't commit.
   - **Editor B:** `SELECT Id, Name FROM dbo.Projects WHERE Id = 1;`. It **hangs** (spinner). It's waiting for A's lock.
   - **Editor B (or a third tab), the investigation query:**
     ```sql
     SELECT r.session_id, r.blocking_session_id, r.wait_type, r.wait_time AS wait_ms, t.text
     FROM sys.dm_exec_requests AS r
     CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
     WHERE r.blocking_session_id <> 0;
     ```
     It shows who waits (`session_id`), who blocks (`blocking_session_id`), and the waiting SQL.
   - **Editor A:** `ROLLBACK TRANSACTION;`. B's query finishes immediately and shows the **old** name (B never saw the uncommitted change: Isolation).
   - Bonus: while A holds the lock, `... WHERE Id = 2` in B answers at once. Only the row is locked, not the table.
4. **The NOT IN trap.** Run S5 and S5b. Explain why S5 returns 0 rows.
5. **Write your own query and send it to me:** "projects with their number of **overdue** tasks, **only** projects that have at least one". (Hint: REPORT 1's WHERE + GROUP BY + HAVING. Expected: Mobile app 2, Website redesign 1.)

## 12. CHECK: answer these in your own words

1. **Why is a JOIN needed?** (The checkpoint.) What would you do without it, and why is that bad?
2. INNER JOIN vs LEFT JOIN: when do you use which? Give a ProjectHub example.
3. Why does `LEFT JOIN ... WHERE t.Status <> 2` lose projects without tasks? Where does the condition belong?
4. `COUNT(*)` vs `COUNT(t.Id)`: when do they differ?
5. `WHERE` vs `HAVING`?
6. What does `EXISTS` do, and what's its LINQ twin? Why avoid `NOT IN (subquery)`?
7. **What does a transaction protect?** (The checkpoint.) Explain atomicity and isolation with "delete a project and its tasks".
8. In SQL Server, does an error inside a transaction undo the earlier statements? What do you write so it does?
9. Why must transactions be short? What happens to other sessions meanwhile?
10. What does EF Core's `SaveChanges` do with transactions?
