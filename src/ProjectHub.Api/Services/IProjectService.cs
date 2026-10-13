using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Services;

public interface IProjectService
{
    IReadOnlyList<Project> GetAll();

    // Returns null when the project does not exist: "not found" is a normal answer here.
    Project? GetById(int id);

    // Throws BusinessRuleException when the name is empty, too long, or already used.
    Project Create(string name, string? description);

    // Throws NotFoundException when the project does not exist.
    TaskItem AddTask(int projectId, string title);
}
