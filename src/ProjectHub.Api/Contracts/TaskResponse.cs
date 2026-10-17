using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Contracts;

public record TaskResponse(int Id, int ProjectId, string Title, TaskItemStatus Status, DateTime CreatedAt, DateTime? DueDate);
