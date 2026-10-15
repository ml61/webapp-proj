using ProjectHub.Api.Entities;
using ProjectHub.Api.Exceptions;

namespace ProjectHub.Api.Services;

// In-memory implementation. Topic 10 replaces the List with EF Core + SQL Server.
// It pretends to be a database: each call can wait for a simulated "round-trip" (simulatedLatency).
public class ProjectService : IProjectService
{
    public const int MaxNameLength = 100;

    private readonly List<Project> _projects;
    private readonly TimeSpan _simulatedLatency;

    // Async callers can run at the same time on different threads, so every access to the
    // shared list and id counters happens inside lock (_gate): one thread at a time.
    private readonly Lock _gate = new();
    private int _nextProjectId;
    private int _nextTaskId;

    public ProjectService(IEnumerable<Project> initialProjects, TimeSpan simulatedLatency = default)
    {
        _projects = initialProjects.ToList();
        _simulatedLatency = simulatedLatency;

        // DefaultIfEmpty(0): Max() on an empty sequence would throw (Topic 2 gotcha).
        _nextProjectId = _projects.Select(p => p.Id).DefaultIfEmpty(0).Max() + 1;
        _nextTaskId = _projects.SelectMany(p => p.Tasks).Select(t => t.Id).DefaultIfEmpty(0).Max() + 1;
    }

    public async Task<IReadOnlyList<Project>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            // A snapshot copy: safe to loop over even if another caller adds a project meanwhile.
            return _projects.ToList().AsReadOnly();
        }
    }

    public async Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            return FindById(id);
        }
    }

    public async Task<Project> CreateAsync(string name, string? description, CancellationToken cancellationToken = default)
    {
        // Validate the input first: no point "calling the database" with a bad request.
        var trimmedName = ValidateName(name);

        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            // Check AND add inside the same lock: otherwise two concurrent calls with the same name
            // could both pass the check before either one adds (a "check-then-act" race).
            EnsureNameIsFree(trimmedName, exceptProjectId: null);

            var project = new Project
            {
                Id = _nextProjectId++,
                Name = trimmedName,
                Description = description,
            };
            _projects.Add(project);
            return project;
        }
    }

    public async Task<Project> UpdateAsync(int id, string name, string? description, CancellationToken cancellationToken = default)
    {
        var trimmedName = ValidateName(name);

        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            var project = FindById(id) ?? throw new NotFoundException(nameof(Project), id);

            // The project may keep its own name; it may not take a name used by ANOTHER project.
            EnsureNameIsFree(trimmedName, exceptProjectId: id);

            project.Name = trimmedName;
            project.Description = description;
            return project;
        }
    }

    public async Task DeleteAsync(int id, CancellationToken cancellationToken = default)
    {
        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            var project = FindById(id) ?? throw new NotFoundException(nameof(Project), id);
            _projects.Remove(project);
        }
    }

    public async Task<TaskItem> AddTaskAsync(int projectId, string title, CancellationToken cancellationToken = default)
    {
        var trimmedTitle = title.Trim();
        if (trimmedTitle.Length == 0)
        {
            throw new BusinessRuleException("Task title is required.");
        }

        await SimulateDatabaseCallAsync(cancellationToken);

        lock (_gate)
        {
            var project = FindById(projectId) ?? throw new NotFoundException(nameof(Project), projectId);

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

    // Call only while holding _gate.
    private Project? FindById(int id) => _projects.SingleOrDefault(p => p.Id == id);

    // Call only while holding _gate. The business rule: project names are unique, ignoring case.
    private void EnsureNameIsFree(string name, int? exceptProjectId)
    {
        if (_projects.Any(p => p.Id != exceptProjectId
                               && string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase)))
        {
            throw new ConflictException($"A project named '{name}' already exists.");
        }
    }

    private static string ValidateName(string name)
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

        return trimmedName;
    }

    // Stands in for the network + database time of a real query. Task.Delay honours the token:
    // if the caller cancels, it stops waiting and throws OperationCanceledException.
    private Task SimulateDatabaseCallAsync(CancellationToken cancellationToken) =>
        Task.Delay(_simulatedLatency, cancellationToken);
}
