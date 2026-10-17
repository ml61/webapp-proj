"""Study book for Topic 9: JOINs, GROUP BY/HAVING, subqueries/EXISTS, transactions.

Usage (from repo root):
  python3 scripts/studybooks/09-joins-grouping-transactions.py docs/studybooks/09-joins-grouping-transactions.pdf
SQL scripts are read from git at TOPIC_REV; real runs from docs/studybooks/notes/09-sql-run.txt and 09-blocking.txt.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

OUT = sys.argv[1]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOPIC_REV = "6a31860"   # last change of sql/06-10 in topic 9
NOTES = os.path.join(ROOT, "docs/studybooks/notes")


def src(rel):
    return git_show(ROOT, TOPIC_REV, rel)


def note_file(name):
    with open(os.path.join(NOTES, name), encoding="utf-8") as f:
        return f.read()


def run_section(name):
    """One script's output from 09-sql-run.txt (sections start with '=== sql/<file>')."""
    parts = re.split(r"^=== sql/(\S+)$", note_file("09-sql-run.txt"), flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))[name].strip("\n")


def strip_header(sql):
    """Drop the leading comment block and the USE/GO lines (the book explains them in prose)."""
    lines = sql.splitlines()
    while lines and (lines[0].startswith("--") or not lines[0].strip() or lines[0] in ("USE ProjectHubDb;", "GO")):
        lines.pop(0)
    return "\n".join(lines)


def blocking_part(marker_from, marker_to=None):
    text = note_file("09-blocking.txt")
    start = text.index(marker_from) + len(marker_from)
    end = text.index(marker_to, start) if marker_to else len(text)
    return text[start:end].strip("\n")


S = Story()

# ---------------------------------------------------------------- COVER
S += cover("Study book", "Topic 9: JOINs, GROUP BY, subqueries, transactions",
           "ProjectHub learning track: React/TypeScript to C#/.NET backend. Week 2, topic 9 of 20.")
S += NOTE([
    "**What this lesson is about.** Questions that span **two tables** (JOIN), questions that **summarize** (GROUP BY, HAVING, aggregates), "
    "questions about **existence** (subqueries, EXISTS), and changes that must happen **all or nothing** (transactions, locks).",
    "**What we built.** `sql/06`: a schema change (`DueDate`) on a table with data, what an EF migration does. `sql/07`–`10`: JOINs and "
    "**Report 1: overdue tasks**, GROUP BY and **Report 2: tasks per project**, subqueries and EXISTS, transactions. Plus a real **blocking experiment** with two sessions.",
    "**Checkpoint:** explain **why a JOIN is needed** and **what a transaction protects**. Passed after one re-check round.",
    "**Four traps** run through the whole topic, and three of them are Topic 8's NULL rule in disguise: the **LEFT JOIN + WHERE** trap, the **COUNT(*)** trap, "
    "the **NOT IN** trap, and SQL Server's \"**an error doesn't undo the transaction**\" trap.",
    "**Why it matters for C#:** in Topics 10–11, EF Core generates all of this. `Include` and navigation properties become JOINs, `GroupBy` becomes GROUP BY, "
    "`Any()` becomes EXISTS, and `SaveChanges` runs in a transaction.",
], "Brief overview")
S += H2("Contents")
S += TABLE([
    ["Part", "What is inside"],
    ["1", "Why a JOIN is needed: normalization, the N+1 alternative (the checkpoint)"],
    ["2", "INNER vs LEFT JOIN, aliases, the ON vs WHERE trap"],
    ["3", "The full logical order of a query"],
    ["4", "GROUP BY, aggregates, COUNT(*) vs COUNT(col), HAVING, conditional aggregation"],
    ["5", "Subqueries, IN, EXISTS, the NOT IN trap"],
    ["6", "Transactions: ACID, autocommit, the XACT_ABORT trap, the correct pattern, EF Core (the checkpoint)"],
    ["7", "Locks and isolation: the real blocking experiment"],
    ["8", "Our scripts (06–10) and their real output"],
    ["9", "DEBUG tasks with answers"],
    ["10", "Your answers, corrections, interview Q&A"],
    ["11", "Summary, cheat sheet, checklist, what comes next"],
], [20, 150])
S += PageBreak()

# ---------------------------------------------------------------- PART 1
S += H1("Part 1. Why a JOIN is needed")
S += P("In Topic 8 we split the data on purpose: a project's name is stored **once**, in `Projects`. A task stores only `ProjectId`. "
       "This is **normalization**: each fact lives in one place, so renaming a project is **one** UPDATE, not one per task, "
       "and two copies can never disagree.")
S += P("The price: \"show tasks **with their project name**\" needs **both** tables. A JOIN puts the rows back together through the foreign key:")
S += CODE("""
SELECT t.Id, t.Title, p.Name AS ProjectName
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId;
""")
S += P("**In TypeScript terms**, it's the lookup you'd write in the frontend, but done **inside the database, in one query**:")
S += CODE("""
const projectsById = new Map(projects.map(p => [p.id, p]));
const rows = tasks.map(t => ({ ...t, projectName: projectsById.get(t.projectId)!.name }));
""")
S += H2("1.1 The alternatives without a JOIN, and why they're bad")
S += TABLE([
    ["Alternative", "What happens", "Problem"],
    ["**N+1 queries**", "1 query for the tasks, then 1 query **per task** for its project", "7 tasks = 8 round trips; 1,000 tasks = 1,001. Each costs network time. The classic ORM performance bug (Topic 11)"],
    ["**Duplicated data**", "copy `ProjectName` into every task row", "a rename must update every copy; miss one and the data disagrees with itself"],
    ["**JOIN**", "one query; the database matches FK = PK (using `IX_Tasks_ProjectId` or a hash match)", "none: this is what databases are built for"],
], [32, 70, 68])
S += WARN([
    "Your first answer said that without a JOIN \"the DB would need to scan one table, then the second, and match them\". "
    "That is actually what a JOIN **does inside** the database (one of its strategies). Without a JOIN, the extra work moves into **your code**: N+1 round trips. "
    "Your re-check answer got it right: *\"without it WE would need to query one table, and then query per each row\"*.",
], "Your first answer, corrected")
S += OK([
    "**Why is a JOIN needed?** The data is split across tables so each fact is stored once (normalization). A JOIN combines the rows again "
    "**in one query** by matching the FK to the PK. Without it you'd need N+1 queries from the application, or duplicated data.",
], "Checkpoint answer, part 1")
S += bullets([
    "**Aliases** (`AS t`, `AS p`) are short names for the tables. With two tables, always write `t.Title`: both tables have `Id` and `CreatedAt`, so a bare `Id` is an **ambiguous column** error.",
    "**`ON`** says how rows match: almost always **FK = PK**.",
])

# ---------------------------------------------------------------- PART 2
S += H1("Part 2. INNER JOIN vs LEFT JOIN")
S += TABLE([
    ["", "Keeps", "Our data"],
    ["**INNER JOIN**", "only rows with a match **on both sides**", "7 rows; \"Internal tools\" (no tasks) is **missing**"],
    ["**LEFT JOIN**", "**every row of the left table** (the one after FROM), matched where possible, otherwise **NULL** in the right table's columns", "8 rows: \"Internal tools\" once, with `TaskId` and `Title` NULL"],
], [28, 82, 60])
S += CODE("""
Projects LEFT JOIN Tasks:

 Website redesign -- Design mockups
 Website redesign -- Build landing page        INNER JOIN keeps only rows with a match
 Website redesign -- SEO audit                 on both sides: these 7.
 Website redesign -- Write copy
 Mobile app       -- Login screen
 Mobile app       -- Push notifications
 Mobile app       -- App store listing
 Internal tools   -- NULL                       <- only LEFT JOIN keeps this one
""")
S += bullets([
    "**How to choose:** \"should a project with **zero** tasks still appear?\" Yes (reports, dashboards): LEFT. No (tasks with their project name): INNER.",
    "`RIGHT JOIN` = LEFT JOIN with the tables swapped (write it as LEFT). `FULL JOIN` keeps unmatched rows of both sides. `CROSS JOIN` pairs every row with every row. Rarely needed.",
    "**LINQ:** INNER = `Join(...)`. LEFT = `GroupJoin(...).SelectMany(..., DefaultIfEmpty())` (awkward). With EF Core you write `t.Project.Name` and EF writes the JOIN (Topic 11).",
])
S += WARN([
    "You answered \"inner join when I need only **truthy** rows, left join **all** rows\". Two fixes: INNER keeps rows with a **match on both sides** (nothing to do with truthiness), "
    "and LEFT keeps all rows **of the left table**, not of both tables.",
], "Your answer, sharpened")
S += H2("2.1 The LEFT JOIN trap: ON vs WHERE")
S += P("\"Every project, with its **open** tasks\":")
S += CODE("""
-- J3a, WRONG: "Internal tools" disappears
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id
WHERE t.Status <> 2

-- J3b, RIGHT: the condition decides WHICH TASKS match; every project stays
FROM dbo.Projects AS p
LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id AND t.Status <> 2
""")
S += P("**Why:** WHERE runs **after** the join. The \"Internal tools\" row has `t.Status = NULL`, and `NULL <> 2` is **UNKNOWN** (Topic 8's three-valued logic). "
       "WHERE keeps only TRUE rows, so the row is thrown away, and the LEFT JOIN silently became an INNER JOIN. Real result: J3a 5 rows, J3b 6 rows.")
S += OK(["In a LEFT JOIN, conditions on the **right** table go in **ON**. Conditions in WHERE on the right table undo the LEFT."], "Rule")
S += PageBreak()

# ---------------------------------------------------------------- PART 3
S += H1("Part 3. The full logical order of a query")
S += CODE("""
FROM / JOIN  ->  WHERE  ->  GROUP BY  ->  HAVING  ->  SELECT  ->  ORDER BY  ->  OFFSET / FETCH
 which rows      filter     make         filter      compute     sort          page
 (combined)      rows       groups       groups      columns
""")
S += P("Most rules of this topic follow from this one picture:")
S += bullets([
    "`WHERE COUNT(*) > 2` is an **error**: when WHERE runs, nothing has been counted yet. Use HAVING.",
    "A SELECT alias (`AS DaysOverdue`) can't be used in WHERE (SELECT runs later), but it can be used in ORDER BY.",
    "The LEFT JOIN trap: WHERE runs **after** the JOIN.",
    "LINQ's method chain (`Where` before `GroupBy` before `Select`) follows the same order. That's why it feels natural once you know SQL's real order.",
])

# ---------------------------------------------------------------- PART 4
S += H1("Part 4. GROUP BY and aggregates")
S += P("**Aggregates** turn many rows into one value: `COUNT`, `SUM`, `MIN`, `MAX`, `AVG`. **GROUP BY** = \"one output row **per distinct value**\", "
       "like JS `Object.groupBy(tasks, t => t.status)` followed by a count per group.")
S += TABLE([
    ["SQL", "LINQ"],
    ["`SELECT COUNT(*) FROM dbo.Tasks`", "`tasks.Count()`"],
    ["`SELECT MAX(CreatedAt) FROM dbo.Tasks`", "`tasks.Max(t => t.CreatedAt)`"],
    ["`SELECT Status, COUNT(*) FROM dbo.Tasks GROUP BY Status`", "`tasks.GroupBy(t => t.Status).Select(g => new { g.Key, Count = g.Count() })`"],
    ["`... WHERE ... GROUP BY ... HAVING COUNT(*) > 2`", "`.Where(...).GroupBy(...).Where(g => g.Count() > 2)`"],
], [82, 88])
S += P("**The rule:** every column in SELECT is either **in GROUP BY** or **inside an aggregate**. `SELECT Status, Title, COUNT(*) ... GROUP BY Status` is an error: "
       "a group of 3 Todo tasks has 3 different titles, and the database won't guess which one to show.")
S += H2("4.1 COUNT(*) vs COUNT(column): the second trap")
S += bullets([
    "`COUNT(*)` counts **rows**.",
    "`COUNT(column)` counts **non-NULL values** in that column. G1: `COUNT(*)` = 7, `COUNT(DueDate)` = **6** (task 6 has no due date).",
])
S += P("After a LEFT JOIN they differ exactly where it hurts. \"Internal tools\" has **one row** (filled with NULLs), so `COUNT(*)` says **1 task**:")
S += CODE("""
Name             Tasks_WRONG Tasks_RIGHT
Internal tools   1           0
Mobile app       3           3
Website redesign 4           4
""", "Real output of G3: COUNT(*) vs COUNT(t.Id)")
S += OK(["After a LEFT JOIN, count a column of the right table (`COUNT(t.Id)`), never `COUNT(*)`."], "Rule")
S += WARN([
    "You wrote: \"`*` counts all rows, even unreal ones (**falsy**); `t.Id` all valid **truthy** rows\". The idea is right, but drop the JS words in SQL. "
    "`COUNT(col)` skips **only NULL**. A `0` or an empty string `''` **is** counted, although both are falsy in JS. Saying \"falsy\" in an interview signals JS thinking.",
], "Your answer, sharpened")
S += H2("4.2 HAVING = WHERE for groups")
S += CODE("""
WHERE t.Status <> 2          -- filters ROWS, before grouping (drop Done tasks)
GROUP BY p.Id, p.Name
HAVING COUNT(*) > 2          -- filters GROUPS, after counting
""")
S += P("G4 result: only **Mobile app** (3 open tasks). Website redesign has 2 open tasks, so `> 2` drops it.")
S += H2("4.3 Conditional aggregation: several counts in one pass")
S += CODE("SUM(CASE WHEN t.Status = 0 THEN 1 ELSE 0 END) AS Todo")
S += P("`CASE WHEN ... THEN ... ELSE ... END` is SQL's ternary (`status === 0 ? 1 : 0`). Summing the 1s counts the Todo tasks. One CASE per status "
       "gives a full status breakdown per project in **one query**: that's **Report 2**. For \"Internal tools\" `t.Status` is NULL, so every CASE takes the ELSE (0).")
S += PageBreak()

# ---------------------------------------------------------------- PART 5
S += H1("Part 5. Subqueries and EXISTS")
S += P("A **subquery** is a query inside another query, in parentheses.")
S += TABLE([
    ["Kind", "Returns", "Example (script 09)", "LINQ"],
    ["**scalar**", "one value", "`WHERE CreatedAt = (SELECT MAX(CreatedAt) FROM dbo.Tasks)`", "`var max = tasks.Max(...); tasks.Where(t => t.CreatedAt == max)`"],
    ["**IN**", "a list", "`WHERE Id IN (SELECT ProjectId FROM dbo.Tasks WHERE Status = 2)`", "`ids.Contains(p.Id)`"],
    ["**EXISTS**", "true / false", "`WHERE EXISTS (SELECT 1 FROM dbo.Tasks AS t WHERE t.ProjectId = p.Id AND ...)`", "`tasks.Any(t => t.ProjectId == p.Id && ...)`"],
], [18, 20, 72, 60])
S += P("**EXISTS** is SQL's `.some()` / `.Any()`: \"does the subquery return **at least one row**?\"")
S += bullets([
    "The subquery uses `p.Id` from the **outer** query: a **correlated** subquery, checked once per project.",
    "`SELECT 1` is a convention: EXISTS ignores what's selected and only checks whether a row exists.",
    "The database can **stop at the first match**. `COUNT(*) > 0` would count them all, so EXISTS is the better way to ask \"is there any?\".",
    "`NOT EXISTS` = \"has **no** matching row\". `LEFT JOIN ... WHERE t.Id IS NULL` gives the same answer (S4 shows both). You'll see both styles in real code.",
])
S += H2("5.1 The NOT IN trap (NULL trap number three)")
S += P("`x NOT IN (a, b, NULL)` means `x <> a AND x <> b AND x <> NULL`. The last part is UNKNOWN, so the whole condition is **never TRUE**, and you get **0 rows** with no error.")
S += P("S5 asks: \"tasks whose due date is **not** one of project 2's due dates\". Project 2's due dates are (2026-09-30, **NULL**, 2026-10-10), because task 6 has no due date. "
       "Result: **0 rows**. S5b asks the same question with `NOT EXISTS`: tasks 1–4.")
S += OK(["Use `NOT EXISTS` instead of `NOT IN (subquery)`, unless the subquery's column is `NOT NULL`."], "Rule")
S += NOTE([
    "All three NULL traps of this topic come from one rule from Topic 8: **comparisons with NULL are UNKNOWN, and WHERE keeps only TRUE**.",
    "**1.** The LEFT JOIN + WHERE trap: `NULL <> 2` drops the unmatched row. **2.** The `<>` trap (Topic 8): `<> N'x'` skips NULL rows. **3.** The NOT IN trap: one NULL in the list makes everything UNKNOWN.",
    "COUNT is different: it's not a comparison. `COUNT(col)` simply **skips** NULLs.",
], "One rule, three traps")

# ---------------------------------------------------------------- PART 6
S += H1("Part 6. Transactions")
S += P("**A transaction groups several statements into one unit: all of them happen, or none do.**")
S += P("Example: \"delete project 1\" is **two** statements, because the FK (Topic 8, C5) forces you to delete its tasks first:")
S += CODE("""
BEGIN TRANSACTION;
    DELETE FROM dbo.Tasks    WHERE ProjectId = 1;
    DELETE FROM dbo.Projects WHERE Id = 1;
COMMIT TRANSACTION;     -- make it permanent    (or ROLLBACK TRANSACTION: undo everything since BEGIN)
""")
S += P("If the connection drops, the server crashes, or the second statement fails **between** them, the tasks are gone and the project remains: "
       "half an operation that nothing will ever fix. **TS analogy:** like building a new state object and calling `setState` once at the end, "
       "so the UI never sees a half-updated state. (A `Promise.all` doesn't give you that; a transaction does.)")
S += H2("6.1 ACID: what a transaction protects (interview classic)")
S += TABLE([
    ["Letter", "Means", "ProjectHub example"],
    ["**A**tomicity", "all or nothing", "tasks and project are deleted together, or neither"],
    ["**C**onsistency", "valid state before and after; constraints hold at the end", "no task points to a deleted project"],
    ["**I**solation", "other sessions don't see your half-done work", "another request never sees \"tasks gone, project still there\"; it waits on the lock"],
    ["**D**urability", "once COMMIT returns, it survives a crash", "written to the transaction log on disk"],
], [28, 66, 76])
S += OK([
    "**What does a transaction protect?** A **multi-step change**. **Atomicity:** all steps happen or none (no half-deleted project). "
    "**Isolation:** nobody sees or overwrites the half-done state; other sessions wait for COMMIT or ROLLBACK.",
], "Checkpoint answer, part 2")
S += P("**Your answer** (CHECK 7) explained atomicity with exactly our example: *\"1st tasks are deleted and at that moment some problem can occur with the connection, "
       "so the second part is never done, and we end up with a project without tasks instead of a fully removed project. It guarantees no half-jobs.\"* "
       "Isolation was missing, and the re-check (b) added it: the other request waits until the transaction is committed or rolled back.")
S += H2("6.2 Autocommit: you've used transactions all along")
S += P("Without `BEGIN TRANSACTION`, SQL Server runs **each statement as its own transaction** (autocommit). That's why in Topic 8 a failed INSERT left nothing behind "
       "(\"The statement has been terminated\"). You need `BEGIN TRANSACTION` only when **several** statements must stay together.")
S += H2("6.3 The SQL Server trap: an error does NOT undo the transaction")
S += P("By default (`XACT_ABORT OFF`), an error like 547 cancels **only the failing statement**. The transaction stays open, the earlier statements are still there, "
       "and a COMMIT would save half the work. T2 proved it:")
S += CODE("""
ErrorNumber XactState ProjectStillThere
----------- --------- -----------------
547         1         1
""", "T2 real output: after the error the transaction is still committable (1) and the half-created project exists")
S += TABLE([
    ["Function", "Values"],
    ["`@@TRANCOUNT`", "number of open transactions in this session (0 = none)"],
    ["`XACT_STATE()`", "**1** = open and committable; **-1** = open but doomed (only ROLLBACK allowed); **0** = no transaction"],
], [36, 134])
S += H2("6.4 The correct pattern")
S += CODE("""
SET XACT_ABORT ON;                 -- any error dooms the WHOLE transaction (XACT_STATE() = -1)
BEGIN TRY
    BEGIN TRANSACTION;
    -- ... several statements ...
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;                         -- re-raise, like C# "throw;" (Topic 3)
END CATCH;
""")
S += P("T3 real output: error **547**, `XACT_STATE() = -1`, rolled back. The final check found **0** demo projects: nothing half-done was left behind.")
S += WARN([
    "You answered CHECK 8 with \"no, we need to rollback in catch\". \"No\" is right, but the pattern has **four** parts: `XACT_ABORT ON` + TRY/CATCH + ROLLBACK if open + **THROW**. "
    "Without THROW the error is swallowed, and the caller (our API) thinks the operation **succeeded**. That's the same reason `catch { }` without `throw;` is a bug in C#.",
], "Your answer was half")
S += H2("6.5 Transactions in C# (Topic 10)")
S += bullets([
    "**`SaveChangesAsync()`** sends **all pending changes** (inserts, updates, deletes) **in one transaction automatically**. All saved, or nothing saved and an exception.",
    "Each `SaveChanges` call is **its own** transaction. Several calls as one unit: `await using var tx = await db.Database.BeginTransactionAsync(); ... await tx.CommitAsync();`. "
    "If you never commit, disposing `tx` rolls back.",
    "Your answer \"committing them\" (CHECK 10) was too vague. The re-check (c) got it right: 1 project + 3 tasks with an invalid third task, so **nothing saved, exception**.",
])
S += PageBreak()

# ---------------------------------------------------------------- PART 7
S += H1("Part 7. Locks and isolation: the real experiment")
S += P("While a transaction changes a row, it holds a **lock** on it until COMMIT or ROLLBACK. SQL Server's default isolation level is **READ COMMITTED**: "
       "you never read uncommitted data, so a reader of that row **waits**. Our database has `READ_COMMITTED_SNAPSHOT` **off** (the on-premises default; "
       "Azure SQL has it on, and then readers see the last committed version instead of waiting).")
S += P("Experiment in the cloud with two sqlcmd sessions. Session A changes project 1 and holds the transaction open for 10 seconds:")
S += CODE(blocking_part("# ---- session A", "# ---- session B"), "Session A (77)")
S += CODE(blocking_part("# ---- session B (started 2 s later)", "# ---- session C"), "Session B (78), started 2 s later, with a 3 s lock timeout")
S += CODE(blocking_part("# ==== output B", "# ==== output C"), "Session B's output: project 1 times out (Msg 1222); project 2 answers at once (only the ROW is locked)")
S += CODE(blocking_part("# ==== output C"), "A third session, 1 s after B started: who is blocked by whom")
S += bullets([
    "`blocking_session_id = 77`: session 78 waits for session 77. `LCK_M_S` = waiting for a **S**hared (read) lock.",
    "The waiting SQL shows `(@1 tinyint)SELECT ... WHERE [Id]=@1`: the server **auto-parameterized** our simple query (Topic 8's parameters, done by the server itself).",
    "**This is how you investigate \"the API hangs\"** in production: `sys.dm_exec_requests` + `blocking_session_id`.",
])
S += OK([
    "**Keep transactions short.** Never wait for a user, an HTTP call or a file inside one.",
    "**Never leave one open.** A forgotten `BEGIN TRAN` in DBeaver blocks your own API. Check with `SELECT @@TRANCOUNT;` before closing an editor.",
], "Rules that follow")
S += PageBreak()

# ---------------------------------------------------------------- PART 8
S += H1("Part 8. Our scripts and their real output")
S += P("Pinned to the commit where Topic 9's SQL was finished. 06 runs from the terminal (`./scripts/run-sql.sh sql/06-add-due-date.sql`); "
       "07–09 run in DBeaver one query at a time; in 10, T1 runs one statement at a time and T2/T3 are selected as whole blocks. "
       "All five ran twice in the cloud with identical results (except `DaysOverdue`, which grows every day).")
S += H2("8.1 06-add-due-date.sql: a schema change on a table with data")
S += CODE(strip_header(src("sql/06-add-due-date.sql")))
S += bullets([
    "`ALTER TABLE ... ADD` changes a table that **already has rows**: what an **EF Core migration** does (Topic 10).",
    "The column is **nullable**, so existing rows simply get NULL. A `NOT NULL` column would need a `DEFAULT` for the existing rows, or the ALTER fails.",
    "`COL_LENGTH(...) IS NULL` = \"the column doesn't exist yet\": the script is **re-runnable** (like `IF DB_ID(...) IS NULL` in 01).",
    "The due dates are chosen to cover every case: overdue (2, 5, 7), past but Done (1, 4), future (3), no due date (6).",
    "`DueDate` exists only in SQL for now. In Topic 10 it's added to the C# `TaskItem` entity, and the EF migration creates the column from there.",
])
OUT06 = run_section("06-add-due-date.sql")
S += CODE(OUT06[OUT06.index("Id Title"):], "Output of 06 (the check SELECT)")
S += H2("8.2 07-joins.sql")
S += CODE(strip_header(src("sql/07-joins.sql")))
S += CODE(run_section("07-joins.sql"), "Output of 07 (run on 17 Oct 2026)")
S += P("**Report 1, read:** three overdue tasks, most overdue first. Not in the report: tasks 1 and 4 (past due but **Done**), task 3 (due in 2027), "
       "task 6 (**no due date**: `NULL < now` is UNKNOWN, which is the behavior we want here).")
S += H2("8.3 08-group-by.sql")
S += CODE(strip_header(src("sql/08-group-by.sql")))
S += CODE(run_section("08-group-by.sql"), "Output of 08")
S += H2("8.4 09-subqueries-exists.sql")
S += CODE(strip_header(src("sql/09-subqueries-exists.sql")))
S += CODE(run_section("09-subqueries-exists.sql"), "Output of 09: S1, S2, S3, S4 (twice), S5 (0 rows: the trap), S5b")
S += H2("8.5 10-transactions.sql")
S += CODE(strip_header(src("sql/10-transactions.sql")))
S += CODE(run_section("10-transactions.sql"), "Output of 10: T1 (1, deletes, 2 projects, rollback, 3 projects, 4 tasks, 0), T2 (547, 1, 1), T3 (547, -1), check 0")
S += NOTE([
    "**My mistake while building 10:** the first version of T2 let the 547 error escape. `run-sql.sh` uses `sqlcmd -b` (\"stop on the first error\"), "
    "so the script stopped there and T3 never ran. Fix: T2 catches its own error too and shows `XACT_STATE() = 1`, which also makes the T2 vs T3 contrast (1 vs -1) visible. "
    "`-b` is right for setup scripts and wrong for scripts that fail on purpose.",
    "Side effect you can spot: T2 and T3 used up identity values. A ROLLBACK doesn't give ids back (Topic 8's gaps).",
], "Building notes")
S += PageBreak()

# ---------------------------------------------------------------- PART 9
S += H1("Part 9. DEBUG tasks with answers")
S += P("No debugger for SQL: you investigate with small queries, the error messages and the server's own views. You went straight to the CHECK, so here are the answers.")
S += TABLE([
    ["Task", "Answer"],
    ["1. LEFT JOIN trap: why does Internal tools vanish in J3a?",
     "Its row has `t.Status = NULL`; WHERE runs after the join; `NULL <> 2` is UNKNOWN; WHERE keeps only TRUE. Put the condition in ON (J3b)."],
    ["2. COUNT trap: why does COUNT(*) say 1 for a project without tasks?",
     "The LEFT JOIN creates one row for it (with NULLs); `COUNT(*)` counts rows. `COUNT(t.Id)` skips the NULL: 0."],
    ["3. Blocking lab (two DBeaver editors)",
     "Editor A: `BEGIN TRANSACTION; UPDATE ... WHERE Id = 1;` (no commit). Editor B: `SELECT ... WHERE Id = 1` hangs. "
     "The `sys.dm_exec_requests` query shows B blocked by A. A: `ROLLBACK` and B finishes with the **old** name. `WHERE Id = 2` in B is not blocked (row lock). Part 7 has the real run."],
    ["4. NOT IN trap: why does S5 return 0 rows?", "Project 2's due dates include NULL; `x NOT IN (a, NULL, b)` contains `x <> NULL`, which is UNKNOWN for every x."],
    ["5. Your query: projects with their number of overdue tasks, only those with at least one", "Below. Result: Mobile app 2, Website redesign 1."],
], [62, 108])
S += CODE("""
SELECT p.Name, COUNT(*) AS OverdueTasks
FROM dbo.Tasks AS t
INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId
WHERE t.DueDate < SYSUTCDATETIME() AND t.Status <> 2     -- rows: overdue tasks only
GROUP BY p.Id, p.Name
HAVING COUNT(*) >= 1;                                     -- groups: at least one
""", "DEBUG task 5 (model answer, verified)")
S += P("**Interview follow-up:** the HAVING is **redundant** here. After an INNER JOIN and that WHERE, every group already has at least one row. "
       "It would matter with a LEFT JOIN (zero-task groups exist) or with a higher threshold (`> 1`).")
S += H2("Investigation toolbox (adds to Topic 8's)")
S += TABLE([
    ["Question", "Tool"],
    ["Is a transaction still open in my session?", "`SELECT @@TRANCOUNT;` (0 = none)"],
    ["Can this transaction still be committed?", "`SELECT XACT_STATE();` (1 yes, -1 doomed, 0 none)"],
    ["Why is my query / the API hanging?", "`sys.dm_exec_requests` with `blocking_session_id <> 0` (+ `sys.dm_exec_sql_text` for the SQL)"],
    ["Does a LEFT JOIN keep the rows I expect?", "count rows with and without the WHERE; check for NULL-filled rows"],
    ["Are my counts right?", "compare `COUNT(*)` with `COUNT(t.Id)`"],
], [72, 98])
S += PageBreak()

# ---------------------------------------------------------------- PART 10
S += H1("Part 10. Your answers, corrections, interview Q&A")
S += H2("10.1 CHECK: your answers")
S += TABLE([
    ["Question", "Your answer", "Verdict / complete answer"],
    ["1. Why a JOIN?", "\"retrieve info from 2 tables in one go; without it the DB would scan one table, then the 2nd, then match\"",
     "**Half:** \"one go\" right; that scanning is what a JOIN does inside. Without it: N+1 queries in your code, or duplicated data. Re-check: **right**"],
    ["2. INNER vs LEFT", "\"inner: only truthy rows; left: all rows\"", "**Half:** match on both sides vs all rows of the LEFT table + NULLs; example missing"],
    ["3. LEFT JOIN + WHERE", "\"WHERE removes the row where status is null; condition belongs to the join\"", "**Right** (in ON)"],
    ["4. COUNT(*) vs COUNT(t.Id)", "\"* all rows even unreal (falsy); t.Id valid truthy rows\"", "**Right idea, wrong words:** COUNT(col) skips only NULL; 0 and '' are counted"],
    ["5. WHERE vs HAVING", "\"having is where but for groups\"", "**Right.** + WHERE runs before grouping, can't use aggregates"],
    ["6. EXISTS, NOT IN", "\"checks if something exists in a list; Any(); NOT IN breaks with NULL\"", "**Right.** + stops at the first match; correlated"],
    ["7. What a transaction protects", "\"no half-jobs\" with the delete-project example", "**Atomicity right.** Isolation missing; re-check (b): **right**"],
    ["8. Does an error undo it?", "\"no, we need to rollback in catch\"", "**Half:** XACT_ABORT ON + TRY/CATCH + ROLLBACK + THROW"],
    ["9. Why short?", "\"they lock, other sessions are waiting\"", "**Right.** + until COMMIT/ROLLBACK; requests hang or time out (1222)"],
    ["10. SaveChanges", "\"committing them\"", "**Too vague:** all pending changes in ONE automatic transaction. Re-check (c): **right**"],
], [30, 66, 74])
S += H2("10.2 Re-check (round 2)")
S += TABLE([
    ["Question", "Your answer", "Verdict"],
    ["a) Why a JOIN, and what without it?", "\"so we receive data matched from 2 tables in one query; without it WE would query one table and then query per row (tasks-project)\"", "**Right** (that's N+1)"],
    ["b) Another request SELECTs project 1 mid-transaction", "\"it waits for the transaction to finish (committed or rolled back)\"", "**Right.** It waits on the lock; old row after ROLLBACK, \"not found\" after COMMIT; may time out"],
    ["c) SaveChanges, 1 project + 3 tasks, 3rd invalid", "\"nothing saved, exception\"", "**Right**"],
], [44, 70, 56])
S += H2("10.3 Mistakes and corrections in this topic")
S += bullets([
    "**You:** \"without a JOIN the DB would scan both tables and match\". Correction: that IS a join's work; without a JOIN the work moves into your code (N+1).",
    "**You:** \"truthy / falsy\" for JOIN and COUNT. Correction: SQL has TRUE / FALSE / UNKNOWN, and COUNT skips only NULL.",
    "**You:** \"rollback in catch\" as the whole pattern. Correction: XACT_ABORT ON + ROLLBACK if open + THROW.",
    "**Me:** T2 first let its error escape; `sqlcmd -b` stopped the script before T3. Fixed by catching it and showing `XACT_STATE()`.",
])
S += H2("10.4 Interview questions with model answers")
qa = [
    ("Why is a JOIN needed?",
     "Data is normalized: each fact is stored once (the project name in Projects, only ProjectId in Tasks). A JOIN combines the rows in one query by matching FK to PK. "
     "Without it: N+1 queries from the application, or duplicated data that can disagree."),
    ("INNER JOIN vs LEFT JOIN?",
     "INNER keeps rows with a match on both sides. LEFT keeps every row of the left table, with NULLs where there's no match. Tasks with project names: INNER. A per-project report including projects with 0 tasks: LEFT."),
    ("Why does a WHERE on the right table break a LEFT JOIN?",
     "WHERE runs after the join; the unmatched rows have NULLs there, NULL comparisons are UNKNOWN, and WHERE drops them, so it becomes an INNER JOIN. Put the condition in ON."),
    ("COUNT(*) vs COUNT(column)?",
     "COUNT(*) counts rows; COUNT(column) counts non-NULL values. After a LEFT JOIN, COUNT(*) gives 1 for a parent without children; count a right-table column instead."),
    ("WHERE vs HAVING?",
     "WHERE filters rows before grouping and can't use aggregates; HAVING filters groups after aggregation."),
    ("What's the logical order of a SELECT?",
     "FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, OFFSET/FETCH. Hence no aggregates in WHERE and no SELECT aliases in WHERE."),
    ("What does EXISTS do? Why prefer NOT EXISTS to NOT IN?",
     "EXISTS is true if the subquery returns at least one row and can stop at the first match (LINQ Any()). NOT IN returns nothing if the list contains a NULL; NOT EXISTS doesn't have that problem."),
    ("What does a transaction protect? Explain ACID.",
     "A multi-step change. Atomicity: all or nothing. Consistency: constraints hold before and after. Isolation: others don't see the half-done state. Durability: committed data survives a crash."),
    ("Does an error inside a transaction roll it back in SQL Server?",
     "Not by default: only the failing statement is cancelled and the transaction stays open (XACT_STATE 1). Use SET XACT_ABORT ON with TRY/CATCH, ROLLBACK if @@TRANCOUNT > 0, and THROW."),
    ("Why keep transactions short?",
     "Locks are held until COMMIT/ROLLBACK; other sessions wait (READ COMMITTED) and requests hang or time out. Never wait for users or external calls inside a transaction."),
    ("How do you find out why queries are hanging?",
     "sys.dm_exec_requests where blocking_session_id <> 0 shows who waits on whom and the wait type (e.g. LCK_M_S); sys.dm_exec_sql_text shows the SQL."),
    ("What does EF Core's SaveChanges do with transactions?",
     "It sends all pending changes in one transaction automatically: all saved or none, plus an exception. Several SaveChanges as one unit: Database.BeginTransactionAsync() + CommitAsync()."),
    ("What is the N+1 problem?",
     "Loading a list with one query and then each item's related data with one query per item: N+1 round trips instead of one JOIN. Common with ORM lazy loading (Topic 11)."),
    ("How do you add a column to a table that already has data?",
     "ALTER TABLE ... ADD. Nullable: existing rows get NULL. NOT NULL: give a DEFAULT. In EF Core this is a migration."),
]
for q, a in qa:
    S += QA(q, a)

# ---------------------------------------------------------------- PART 11
S += PageBreak()
S += H1("Part 11. Summary")
S += OK([
    "**JOIN:** data is normalized (each fact once); a JOIN recombines it in one query, FK = PK. The alternative is N+1 queries.",
    "**INNER** = matches on both sides; **LEFT** = all left rows + NULLs. Right-table conditions of a LEFT JOIN go in **ON**.",
    "**Order:** FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, OFFSET/FETCH.",
    "**GROUP BY:** every SELECT column grouped or aggregated; **HAVING** filters groups; **COUNT(t.Id)** after a LEFT JOIN; CASE + SUM for several counts.",
    "**EXISTS** = Any(), stops at the first match; **NOT EXISTS** instead of NOT IN (NULL trap).",
    "**Transactions** protect multi-step changes: atomicity (all or nothing) + isolation (no half-done state visible).",
    "**SQL Server:** an error doesn't undo the transaction; use XACT_ABORT ON + TRY/CATCH + ROLLBACK + THROW.",
    "**Locks** last until COMMIT/ROLLBACK: keep transactions short; find blockers with `sys.dm_exec_requests`.",
    "**EF Core:** navigation properties become JOINs, `Any()` becomes EXISTS, `SaveChanges` = one transaction.",
], "Key takeaways")
S += H2("Cheat sheet")
S += TABLE([
    ["Need", "SQL"],
    ["rows of two tables", "`FROM dbo.Tasks AS t INNER JOIN dbo.Projects AS p ON p.Id = t.ProjectId`"],
    ["keep parents without children", "`FROM dbo.Projects AS p LEFT JOIN dbo.Tasks AS t ON t.ProjectId = p.Id`"],
    ["filter the right side of a LEFT JOIN", "`... ON t.ProjectId = p.Id AND t.Status <> 2`"],
    ["count per group", "`SELECT p.Name, COUNT(t.Id) ... GROUP BY p.Id, p.Name`"],
    ["filter groups", "`HAVING COUNT(*) > 2`"],
    ["count by condition", "`SUM(CASE WHEN t.Status = 0 THEN 1 ELSE 0 END)`"],
    ["\"has any\" / \"has none\"", "`WHERE [NOT] EXISTS (SELECT 1 FROM dbo.Tasks AS t WHERE t.ProjectId = p.Id)`"],
    ["now (UTC), days between", "`SYSUTCDATETIME()`, `DATEDIFF(DAY, a, b)`"],
    ["all or nothing", "`SET XACT_ABORT ON; BEGIN TRY BEGIN TRAN ... COMMIT END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK; THROW; END CATCH`"],
    ["open transactions?", "`SELECT @@TRANCOUNT;`  /  `SELECT XACT_STATE();`"],
    ["who blocks whom", "`SELECT session_id, blocking_session_id, wait_type FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;`"],
    ["add a column", "`ALTER TABLE dbo.Tasks ADD DueDate DATETIME2(7) NULL;`"],
], [48, 122])
S += H2("Checklist: can you do this without notes?")
S += bullets([
    "Explain why a JOIN is needed and what N+1 is.",
    "Write Report 1 (overdue tasks with project names) and say why tasks 1, 3, 4 and 6 are not in it.",
    "Write Report 2 (tasks per project, including projects with no tasks) and explain COUNT(t.Id).",
    "Explain the LEFT JOIN + WHERE trap and the NOT IN trap with the NULL rule.",
    "Explain ACID with \"delete a project and its tasks\".",
    "Write the XACT_ABORT + TRY/CATCH + THROW pattern and say what each line is for.",
    "Explain what another request sees while your transaction runs, and how to find who blocks it.",
    "Say what SaveChanges does with transactions.",
])
S += H2("What comes next: Topic 10 (EF Core basics)")
S += P("Replace the in-memory `ProjectService` storage with SQL Server through **EF Core**: `DbContext`, `DbSet<T>`, the SQL Server provider, the connection string "
       "(the `Database=` part from Topic 8's master trap), and **migrations** that create the schema from the C# entities (including the new `DueDate`). "
       "Checkpoint: the schema comes from a migration, and CRUD persists across restarts.")

build(OUT, S, "ProjectHub study book | Topic 9: JOINs, GROUP BY, subqueries, transactions",
      "ProjectHub study book: Topic 9, JOINs, GROUP BY, subqueries, transactions")
print("ok", OUT)
