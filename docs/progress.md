# Progress

**Current topic:** 10 — EF Core basics: DbContext, DbSet, provider, migrations
**Track:** 4 weeks, 2–3 h/day. Daily loop: LEARN (30–40%) → BUILD (40–50%) → DEBUG (10–20%) → CHECK.

Status: `[ ]` not started · `[~]` in progress · `[x]` checkpoint passed

## Week 1 — C# + debugging
| # | Topic | Build / try | Checkpoint | Status |
|---|---|---|---|---|
| 1 | Setup + C# bridge: types, nullability, classes, records | Create `Project` and `TaskItem`. Set a breakpoint, inspect values | Run the solution; explain class vs record and nullable warnings | [x] |
| 2 | Collections + LINQ: `List<T>`, `Dictionary`, `IEnumerable`, lambdas | Filter, sort, group, project sample ProjectHub data | Translate map/filter/find into LINQ | [x] |
| 3 | Interfaces, generics, exceptions | `IProjectService` + `ProjectService`, one business validation rule | Explain interface vs class; handle an expected error | [x] |
| 4 | Async/await: `Task`, `Task<T>`, I/O, `CancellationToken` | Make service calls async, pass a CancellationToken through one path | Explain why backend I/O should be awaited | [x] |
| 5 | Debugging fundamentals (local) | Debug Lab A | Find a bug without `Console.WriteLine` | [x] |

## Week 2 — ASP.NET Core + SQL + EF Core
| # | Topic | Build / try | Checkpoint | Status |
|---|---|---|---|---|
| 6 | HTTP + REST: routes, verbs, status codes, DTOs, controllers | CRUD endpoints with in-memory storage | GET/POST/PUT/DELETE work with sensible status codes | [x] |
| 7 | DI, middleware, config, `ILogger` | ProjectService into DI; request timing middleware | Explain Scoped vs Transient vs Singleton | [x] |
| 8 | SQL basics: tables, PK/FK, SELECT/WHERE/ORDER BY, INSERT/UPDATE/DELETE | Create ProjectHubDb by hand; write 10 queries (`sql/`) | Query and change data without EF Core | [x] |
| 9 | JOINs, GROUP BY/HAVING, subqueries/EXISTS, transactions | "Tasks per project" + "overdue tasks" reports; BEGIN TRAN + ROLLBACK | Explain why a JOIN is needed and what a transaction protects | [x] |
| 10 | EF Core basics: DbContext, DbSet, provider, migrations | Replace in-memory storage with SQL Server + EF Core | Schema comes from a migration; CRUD persists | [ ] |

## Week 3 — Errors, tests, architecture (+ start React frontend)
| # | Topic | Build / try | Checkpoint | Status |
|---|---|---|---|---|
| 11 | EF query behavior: relationships, projection, tracking, Include, generated SQL | Project → Tasks relation; Select projection vs Include | Inspect the SQL behind a LINQ query | [ ] |
| 12 | Errors + validation: 400/404/409/500, ProblemDetails, global exception handling | Validation + predictable error responses | Bad input never gives a mystery 500 | [ ] |
| 13 | Unit tests: xUnit, Arrange-Act-Assert, Facts/Theories | 8–12 tests for ProjectService rules | Debug one test; explain what is isolated | [ ] |
| 14 | Integration tests: WebApplicationFactory, HttpClient | GET, POST, invalid input, 404 through real HTTP | Tests start the app in memory and verify the HTTP contract | [ ] |
| 15 | Architecture: layered, Clean, Vertical Slice, modular monolith, microservices | Refactor only where code is hard to test/change | Explain trade-offs without "one is always best" | [ ] |
| FE | React + TS frontend in `web/` (extra, not in roadmap) | Vite app, typed client from OpenAPI, CORS | Projects/tasks CRUD from the UI | [ ] |

## Week 4 — Production basics + final ticket
| # | Topic | Build / try | Checkpoint | Status |
|---|---|---|---|---|
| 16 | Auth: authentication vs authorization, 401 vs 403, claims/roles/policies | Protect one endpoint; reproduce 401 and 403 | Explain identity vs permission | [ ] |
| 17 | Logging + observability: levels, structured logging, correlation | Logs around one operation and one error path | Logs explain what happened without secrets | [ ] |
| 18 | SQL performance: indexes, scan vs seek, execution plans | Index for a real filter; inspect the plan | Why indexes help reads and can hurt writes | [ ] |
| 19 | Azure concepts: App Service, Azure SQL, Managed Identity, Key Vault, App Insights | Free reading/modules (deploy optional) | Draw cloud ProjectHub and explain each service | [ ] |
| 20 | **Final ticket:** optional DueDate on tasks (see below) | No tutorial — docs only | Works end-to-end; explain every change | [ ] |

### Final ticket checklist
- [ ] Entity + request/response DTOs changed
- [ ] EF Core migration created and applied
- [ ] Query filter (e.g. due before a date)
- [ ] Equivalent SQL written by hand once
- [ ] Invalid dates → sensible HTTP error
- [ ] Unit tests for the business rule
- [ ] Integration test for the HTTP filter
- [ ] Debugger used at least once while testing
- [ ] Generated SQL inspected
- [ ] One useful structured log, no secrets
- [ ] `dotnet test` all green
- [ ] Can explain every changed file and why

## Readiness checklist (what the interview covers)
- [ ] **C#** — classes/records/interfaces/generics, LINQ, exceptions, nullable types, async/await
- [ ] **ASP.NET** — Program.cs → middleware → route/controller → service
- [ ] **HTTP** — 400 vs 401 vs 403 vs 404 vs 409 vs 500
- [ ] **SQL** — SELECT/JOIN/GROUP BY, update data safely
- [ ] **EF Core** — migrations, async queries, inspect generated SQL
- [ ] **Debug** — breakpoints, Watch, Call Stack, exception settings, logs
- [ ] **Tests** — unit test + WebApplicationFactory integration test
- [ ] **Architecture** — layered vs Clean vs vertical slice vs microservices
- [ ] **Azure** — App Service, Azure SQL, Managed Identity, Key Vault, Application Insights
- [ ] **Independence** — small backend ticket using docs only
