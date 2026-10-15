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
