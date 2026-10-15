using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Services;

// Async because the real implementation (EF Core + SQL Server, Topic 10) does I/O.
// Every method accepts a CancellationToken so a caller can stop work that is no longer needed.
public interface IProjectService
{
    Task<IReadOnlyList<Project>> GetAllAsync(CancellationToken cancellationToken = default);

    // Returns null when the project does not exist: "not found" is a normal answer here.
    Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default);

    // Throws BusinessRuleException when the name is empty or too long, ConflictException when it is already used.
    Task<Project> CreateAsync(string name, string? description, CancellationToken cancellationToken = default);

    // Throws NotFoundException, BusinessRuleException or ConflictException (name used by ANOTHER project).
    Task<Project> UpdateAsync(int id, string name, string? description, CancellationToken cancellationToken = default);

    // Throws NotFoundException when the project does not exist.
    Task DeleteAsync(int id, CancellationToken cancellationToken = default);

    // Throws NotFoundException when the project does not exist.
    Task<TaskItem> AddTaskAsync(int projectId, string title, CancellationToken cancellationToken = default);
}
