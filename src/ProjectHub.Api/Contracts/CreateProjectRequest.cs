namespace ProjectHub.Api.Contracts;

// Body of POST /api/projects. Only what the CLIENT may set: no Id, no CreatedAt (the server decides those).
public record CreateProjectRequest(string Name, string? Description);
