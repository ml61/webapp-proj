namespace ProjectHub.Api.Contracts;

// Body of PUT /api/projects/{id}: the full new state of the editable fields.
public record UpdateProjectRequest(string Name, string? Description);
