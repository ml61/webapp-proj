using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Contracts;

// Entity -> DTO. Extension methods (Topic 2), so a controller can write project.ToResponse().
// The DTOs are NEW objects: callers of the API never get a reference to the stored entities.
public static class ProjectMappings
{
    public static ProjectSummaryResponse ToSummaryResponse(this Project project) => new(
        project.Id,
        project.Name,
        project.Description,
        project.CreatedAt,
        TaskCount: project.Tasks.Count,
        DoneCount: project.Tasks.Count(t => t.Status == TaskItemStatus.Done));

    public static ProjectResponse ToResponse(this Project project) => new(
        project.Id,
        project.Name,
        project.Description,
        project.CreatedAt,
        project.Tasks.Select(t => t.ToResponse()).ToList());

    public static TaskResponse ToResponse(this TaskItem task) => new(
        task.Id,
        task.ProjectId,
        task.Title,
        task.Status,
        task.CreatedAt);
}
