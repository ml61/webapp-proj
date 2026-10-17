namespace ProjectHub.Api.Contracts;

// Body of POST /api/projects/{projectId}/tasks. The project comes from the URL, not from the body.
// DueDate is optional (Topic 10): send it in UTC, e.g. "2026-11-01T17:00:00Z".
public record CreateTaskRequest(string Title, DateTime? DueDate = null);
