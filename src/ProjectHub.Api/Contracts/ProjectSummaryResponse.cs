namespace ProjectHub.Api.Contracts;

// GET /api/projects: a list item. Counts instead of the full task lists keep the list response small.
public record ProjectSummaryResponse(
    int Id,
    string Name,
    string? Description,
    DateTime CreatedAt,
    int TaskCount,
    int DoneCount);
