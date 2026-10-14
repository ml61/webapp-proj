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
