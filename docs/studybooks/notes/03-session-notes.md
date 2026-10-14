# Topic 3: notes for the study book (questions, corrections, requests)

- **Request:** clearly mark that this block is the CONSTRUCTOR of `public class ProjectService : IProjectService`
  (it was unclear at first; understood after thinking):
  `public ProjectService(IEnumerable<Project> initialProjects) { _projects = ...; _nextProjectId = ...; _nextTaskId = ...; }`
  Explain: same name as the class, no return type, runs once per `new`, the only place `readonly` fields can be assigned,
  TS `constructor(...)` equivalent, and contrast with primary constructors (`class NotFoundException(string entityName, object key)`).
- **Question:** `IReadOnlyList<Project> all = service.GetAll();` vs `var all = service.GetAll();` (user prefers var).
  Answer: identical type here (return type is already IReadOnlyList<Project>); the explicit type was for teaching.
  Contrast: `IProjectService service = new ProjectService(...)` vs `var service = new ProjectService(...)` is NOT the same:
  var infers the concrete class `ProjectService`; the explicit interface type limits the code to the contract
  ("program against the interface"). Rule: var when the right side has the type you want; explicit type when you want
  a different (usually more general) type. In real ASP.NET code DI (topic 7) hands you IProjectService anyway.
- **CHECK answers (round 1)** — right: match by declaration (`: IProjectService`, compiler checks members); IComparable
  constraint (CompareTo available, Project -> compile error); throw; vs throw ex;; OrdinalIgnoreCase (Turkish i).
  Interface vs class: right definition + good point (interface-typed variable sees only the contract) but NO concrete
  benefits given -> swap implementations (EF in topic 10), fakes in tests, DI (topic 7), decorators.
  Abstract class: add state/fields + partial implementation; one base class vs many interfaces.
  Expected vs unexpected: expected example ok; no unexpected example -> SingleOrDefault with duplicate Ids
  (InvalidOperationException), Create(null!) -> NullReferenceException on Trim, Max() without DefaultIfEmpty.
  Skipped "which to catch and where": expected -> catch where you can turn it into a 4xx answer (global handler, topic 12);
  unexpected -> don't catch locally, global handler logs + 500.
  null vs throw: answered with mechanics (SingleOrDefault, ?? throw) instead of design: query (null is a valid answer)
  vs command (cannot be performed -> exception forces handling).
  Custom exceptions: said "reusability" -> real reasons: catch by type (expected vs bug), map type -> HTTP status
  without parsing messages, structured data (EntityName, Key).
  Constructor data: did not know -> constructor injection: no hidden hard-coded dependency, tests choose the data,
  source swappable; TS analogy: importing a singleton inside (needs jest.mock) vs receiving it in the constructor.
- **DEBUG (Rider, .NET exception breakpoint on BusinessRuleException):** stopped on the `throw` line in
  ProjectService.Create although the snippet catches it (exception breakpoints stop when THROWN). trimmedName =
  "Mobile app". User sent a screenshot of the Variables panel (not Frames): $exception pseudo-variable; `this` =
  ProjectService instance (expand -> private fields); parameters name/description (icon with parentheses); locals
  trimmedName and project = null (line not executed yet, like count = 0 in topic 1).
  After removing try/catch the user said "compile failed" -> WRONG TERM: build succeeded; the exception was UNHANDLED
  at runtime -> process crashed ("Unhandled exception. ...BusinessRuleException..."), API never started (snippet was
  before app.Run()). Compile time vs runtime. In an HTTP request ASP.NET catches unhandled exceptions per request -> 500,
  server keeps running (topic 12 maps to 4xx).
