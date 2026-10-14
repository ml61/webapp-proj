# Topic 3: notes for the study book (questions, corrections, requests)

- **Request:** clearly mark that this block is the CONSTRUCTOR of `public class ProjectService : IProjectService`
  (it was unclear at first; understood after thinking):
  `public ProjectService(IEnumerable<Project> initialProjects) { _projects = ...; _nextProjectId = ...; _nextTaskId = ...; }`
  Explain: same name as the class, no return type, runs once per `new`, the only place `readonly` fields can be assigned,
  TS `constructor(...)` equivalent, and contrast with primary constructors (`class NotFoundException(string entityName, object key)`).
