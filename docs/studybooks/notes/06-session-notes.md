# Topic 6: notes for the study book (questions, corrections, requests)

- Build: ProjectsController (GET all, GET {id:int}, POST, PUT {id:int}, DELETE {id:int}, POST {id:int}/tasks);
  DTOs in Contracts/ (Create/UpdateProjectRequest, CreateTaskRequest, ProjectSummaryResponse, ProjectResponse,
  TaskResponse) + ProjectMappings extension methods; Program.cs: JsonStringEnumConverter, AddSingleton<IProjectService>;
  service: UpdateAsync, DeleteAsync, ConflictException : BusinessRuleException (409), ValidateName + EnsureNameIsFree
  (exceptProjectId); WeatherForecast template deleted; topic 3 demo LoggingProjectService got Update/Delete pass-throughs.
- Real calls captured in docs/studybooks/notes/06-api-calls.txt (16 requests, all sensible codes). Notables:
  automatic 400 for missing name (errors dictionary, action never runs); broken JSON -> 400; /api/projects/abc -> 404
  with EMPTY body (route constraint :int, no action matched); 201 Location header; DELETE twice -> 204 then 404.
- Tooling gotcha: `pkill -f ProjectHub.Api` killed the shell that ran it (its own command line matched) -> exit 144.
- **Question:** `ProjectsController(IProjectService projects) : ControllerBase` — "ProjectsController inherits ControllerBase
  and therefore has all its methods/properties?" -> YES. Two parts: (1) primary constructor: `projects` usable in every
  method; ASP.NET creates the controller per request and injects IProjectService (DI). (2) `: ControllerBase` =
  inheritance (TS `extends`): Ok/NotFound/NoContent/CreatedAtAction/Problem, HttpContext/Request/Response, User,
  ModelState. TS: `class ProjectsController extends ControllerBase { constructor(private projects: IProjectService)
  { super(); } }`. Same `:` also means "implements an interface" (ProjectService : IProjectService): one base class,
  many interfaces, base class first, I-prefix tells which. Framework base classes (Exception, ControllerBase) are the
  common exception to "prefer composition over inheritance".
  Quick check asked: what does `:` mean in ProjectService : IProjectService vs ProjectsController : ControllerBase.
- **Question:** `NotFound() : Ok(project.ToResponse())` without `this.` — "C# does it for us?" -> YES: bare names resolve
  to members of the current object incl. inherited ones; `Ok(x)` == `this.Ok(x)`. Different from JS/TS where `this.` is
  required (bare `ok()` looks for a variable/global). Lookup order: locals/parameters -> class members (own + inherited)
  -> outer scopes (static, using namespaces). `this.` needed when a parameter/local shadows a field
  (`this.name = name;`) -> one reason for the `_camelCase` field convention. Trap: primary constructor parameter
  `projects` is NOT a field: `this.projects` is a compile error; it's just in scope for the whole class.
- **User request ("add info so I don't forget"):** the controller's Update can catch NotFound/Conflict/BusinessRule
  exceptions because the service threw them. Screenshots (user underlined the throw lines):
  img/06-update-async-throws.png (UpdateAsync: `FindById(id) ?? throw new NotFoundException(...)`,
  `EnsureNameIsFree(trimmedName, exceptProjectId: id)`), img/06-ensure-name-is-free-throws.png
  (`throw new ConflictException(...)`). Include both images + the Update action code in the study book.
  Explanation: throw -> method exits immediately -> exception travels up the call stack until a matching catch ->
  passes through `lock` which is RELEASED automatically (lock = try/finally) -> async: stored in the Task, re-thrown at
  the controller's await -> catch blocks checked top to bottom by TYPE -> Problem(..., code).
  Table: NotFoundException (FindById ?? throw) -> 404; ConflictException (EnsureNameIsFree) -> 409;
  BusinessRuleException (ValidateName) -> 400; anything else -> no matching catch -> 500 from ASP.NET (topic 12).
  Catch order: ConflictException derives from BusinessRuleException, so it must be caught first (else every conflict
  -> 400; compiler refuses the wrong order). Type decides the status code, message goes to `detail` (why custom
  exception types, topic 3). TS analogy: throw new ConflictError deep in a service, `instanceof` in the Express handler.
- **DEBUG (user):** 2 IsCancellationRequested = false (right). 3 automatic 400, breakpoint not hit (right; precision: the
  FRAMEWORK's [ApiController] validation, not our controller code). 4 /abc not hit -> user said "validated, type not ok,
  auto 404" -> WRONG reason: ROUTING, {id:int} doesn't match "abc", no action matches, request never reaches model
  binding / [ApiController] -> empty body, no ProblemDetails (validation would be 400 with errors). 5 swapped catches ->
  CS0160 "A previous catch clause already catches all exceptions of this or of a super type" (right). 6 asked "tell me":
  without JsonStringEnumConverter enums serialize as numbers ("status":2 for Done; Todo=0, InProgress=1, Done=2) ->
  magic numbers for the frontend; inserting a new enum value shifts numbers and silently breaks old clients.
- **CHECK round 1:** 1 mostly right (404 two flavors: no route vs missing resource; 500 = unexpected failure, the
  global handler only writes it). 2 half: 400 = invalid by itself (shape OR values, "   " has a perfect shape),
  409 = valid but conflicts with current state; retrying 400 never works, 409 may later. 3 definition right, verbs
  WRONG ("put/patch") -> GET, PUT, DELETE idempotent; PATCH not necessarily; POST not; retries after timeouts safe for
  PUT/DELETE, POST may duplicate. 4 didn't know -> 201 + Location header (URL from GetById route) + body.
  5 good (no mutable references, no sensitive data exposure) + add over-posting and stable contract.
  6 half: checks REQUESTS (automatic 400), + ProblemDetails, + binding source inference; routing is from
  [Route]/[HttpGet]. 7 mostly right: HttpContext.RequestAborted, cancelled when the client disconnects.
  8 skipped (singleton). 9 wrong reason ("not found first of all") -> route constraint. 10 right.
- **Re-check (all right):** A GET/PUT/DELETE idempotent; retries without duplicates. B 201 + Location (URL to GET the
  new item) + body. C one shared unit; per-request instances would start from fresh sample data, a POSTed project would
  vanish on the next GET (+ shared by parallel requests -> topic 4 lock). D wrong route: `{id:int}` doesn't match
  "abc", no action matches -> routing 404 before model binding, no ProblemDetails body.
