using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;
using ProjectHub.Api.Data;
using ProjectHub.Api.Entities;
using ProjectHub.Api.Exceptions;

namespace ProjectHub.Api.Services;

// The real implementation (Topic 10): EF Core + SQL Server.
// Scoped, like the DbContext it uses: one instance per HTTP request. No lock and no id counters any more:
// the database generates ids (IDENTITY) and handles concurrent requests (transactions, UNIQUE index).
public class ProjectService(ProjectHubDbContext db, ILogger<ProjectService> logger) : IProjectService
{
    public async Task<IReadOnlyList<Project>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        // Include = also load each project's tasks (a JOIN, Topic 9), because the summary shows task counts.
        // Loading ALL tasks just to count them is wasteful: Topic 11 replaces this with a projection.
        // OrderBy: a database has no "natural" order (Topic 8), and the API should return a stable one.
        return await db.Projects
            .Include(p => p.Tasks)
            .OrderBy(p => p.Id)
            .ToListAsync(cancellationToken);
    }

    public async Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        // Ordering inside Include: the tasks come back sorted by Id, not in whatever order the database likes.
        return await db.Projects
            .Include(p => p.Tasks.OrderBy(t => t.Id))
            .SingleOrDefaultAsync(p => p.Id == id, cancellationToken);
    }

    public async Task<Project> CreateAsync(string name, string? description, CancellationToken cancellationToken = default)
    {
        var trimmedName = ProjectRules.ValidateName(name);
        ProjectRules.ValidateDescription(description);

        await EnsureNameIsFreeAsync(trimmedName, exceptProjectId: null, cancellationToken);

        var project = new Project { Name = trimmedName, Description = description };

        // Add = "track this as NEW". Nothing is sent yet. SaveChangesAsync sends the INSERT
        // and copies the generated Id (IDENTITY) back into project.Id.
        db.Projects.Add(project);
        await SaveChangesAsync(trimmedName, cancellationToken);

        logger.LogInformation("Created project {ProjectId} {ProjectName}", project.Id, project.Name);
        return project;
    }

    public async Task<Project> UpdateAsync(int id, string name, string? description, CancellationToken cancellationToken = default)
    {
        var trimmedName = ProjectRules.ValidateName(name);
        ProjectRules.ValidateDescription(description);

        // A loaded entity is TRACKED: EF remembers its original values.
        // The tasks are loaded too because the response includes them.
        var project = await db.Projects
                          .Include(p => p.Tasks.OrderBy(t => t.Id))
                          .SingleOrDefaultAsync(p => p.Id == id, cancellationToken)
                      ?? throw new NotFoundException(nameof(Project), id);

        // The project may keep its own name; it may not take a name used by ANOTHER project.
        await EnsureNameIsFreeAsync(trimmedName, exceptProjectId: id, cancellationToken);

        // Just change the properties. No "Update()" call needed: SaveChangesAsync compares with the original
        // values and sends an UPDATE for the changed columns only.
        project.Name = trimmedName;
        project.Description = description;
        await SaveChangesAsync(trimmedName, cancellationToken);

        logger.LogInformation("Updated project {ProjectId} {ProjectName}", project.Id, project.Name);
        return project;
    }

    public async Task DeleteAsync(int id, CancellationToken cancellationToken = default)
    {
        // FindAsync looks up by primary key (and first checks the entities this DbContext already tracks).
        var project = await db.Projects.FindAsync([id], cancellationToken)
                      ?? throw new NotFoundException(nameof(Project), id);

        // Remove = "track this as DELETED". SaveChangesAsync sends the DELETE.
        // The project's tasks are deleted by the database itself: ON DELETE CASCADE (see ProjectHubDbContext).
        db.Projects.Remove(project);
        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation("Deleted project {ProjectId}", id);
    }

    public async Task<TaskItem> AddTaskAsync(int projectId, string title, DateTime? dueDate = null, CancellationToken cancellationToken = default)
    {
        var trimmedTitle = ProjectRules.ValidateTitle(title);

        // Check first, so a missing project is a clear 404 (otherwise the INSERT would fail with FK error 547).
        if (!await db.Projects.AnyAsync(p => p.Id == projectId, cancellationToken))
        {
            throw new NotFoundException(nameof(Project), projectId);
        }

        var task = new TaskItem { ProjectId = projectId, Title = trimmedTitle, DueDate = dueDate };
        db.Tasks.Add(task);
        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation("Added task {TaskId} to project {ProjectId}", task.Id, task.ProjectId);
        return task;
    }

    // The business rule: project names are unique, ignoring case.
    // "p.Name == name" becomes SQL "Name = @name", and SQL Server's case-insensitive collation does the
    // ignore-case part. (string.Equals(..., StringComparison.OrdinalIgnoreCase) can't be translated to SQL.)
    private async Task EnsureNameIsFreeAsync(string name, int? exceptProjectId, CancellationToken cancellationToken)
    {
        var taken = await db.Projects.AnyAsync(
            p => p.Id != exceptProjectId && p.Name == name, cancellationToken);

        if (taken)
        {
            throw new ConflictException($"A project named '{name}' already exists.");
        }
    }

    // The check above and the INSERT/UPDATE are two separate round trips. Two requests can both pass the check
    // (the Topic 4 race, now across servers). The UNIQUE index stops the second one with SQL error 2601;
    // we turn that into the same ConflictException, so the client still gets a 409, not a 500.
    private async Task SaveChangesAsync(string projectName, CancellationToken cancellationToken)
    {
        try
        {
            await db.SaveChangesAsync(cancellationToken);
        }
        catch (DbUpdateException ex) when (ex.InnerException is SqlException { Number: 2601 or 2627 })
        {
            throw new ConflictException($"A project named '{projectName}' already exists.");
        }
    }
}
