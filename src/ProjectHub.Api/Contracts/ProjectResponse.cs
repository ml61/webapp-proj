namespace ProjectHub.Api.Contracts;

// GET /api/projects/{id}: one project WITH its tasks.
public record ProjectResponse(
    int Id,
    string Name,
    string? Description,
    DateTime CreatedAt,
    IReadOnlyList<TaskResponse> Tasks);
