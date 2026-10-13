using ProjectHub.Api.Entities;
using ProjectHub.Api.Exceptions;

namespace ProjectHub.Api.Services;

// In-memory implementation. Topic 10 replaces the List with EF Core + SQL Server.
// Not thread-safe yet: fine for a single caller, revisited when it becomes a shared service (Topics 6-7).
public class ProjectService : IProjectService
{
    public const int MaxNameLength = 100;

    private readonly List<Project> _projects;
    private int _nextProjectId;
    private int _nextTaskId;

    public ProjectService(IEnumerable<Project> initialProjects)
    {
        _projects = initialProjects.ToList();

        // DefaultIfEmpty(0): Max() on an empty sequence would throw (Topic 2 gotcha).
        _nextProjectId = _projects.Select(p => p.Id).DefaultIfEmpty(0).Max() + 1;
        _nextTaskId = _projects.SelectMany(p => p.Tasks).Select(t => t.Id).DefaultIfEmpty(0).Max() + 1;
    }

    public IReadOnlyList<Project> GetAll() => _projects.AsReadOnly();

    public Project? GetById(int id) => _projects.SingleOrDefault(p => p.Id == id);

    public Project Create(string name, string? description)
    {
        var trimmedName = name.Trim();

        if (trimmedName.Length == 0)
        {
            throw new BusinessRuleException("Project name is required.");
        }

        if (trimmedName.Length > MaxNameLength)
        {
            throw new BusinessRuleException($"Project name must be at most {MaxNameLength} characters.");
        }

        // The business rule: project names are unique, ignoring case ("Website" == "WEBSITE").
        if (_projects.Any(p => string.Equals(p.Name, trimmedName, StringComparison.OrdinalIgnoreCase)))
        {
            throw new BusinessRuleException($"A project named '{trimmedName}' already exists.");
        }

        var project = new Project
        {
            Id = _nextProjectId++,
            Name = trimmedName,
            Description = description,
        };
        _projects.Add(project);
        return project;
    }

    public TaskItem AddTask(int projectId, string title)
    {
        var project = GetById(projectId) ?? throw new NotFoundException(nameof(Project), projectId);

        var trimmedTitle = title.Trim();
        if (trimmedTitle.Length == 0)
        {
            throw new BusinessRuleException("Task title is required.");
        }

        var task = new TaskItem
        {
            Id = _nextTaskId++,
            ProjectId = project.Id,
            Title = trimmedTitle,
        };
        project.Tasks.Add(task);
        return task;
    }
}
