namespace ProjectHub.Api.Contracts;

// Body of POST /api/projects/{projectId}/tasks. The project comes from the URL, not from the body.
public record CreateTaskRequest(string Title);
