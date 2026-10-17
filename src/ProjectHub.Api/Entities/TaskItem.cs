namespace ProjectHub.Api.Entities;

public class TaskItem
{
    public int Id { get; set; }
    public int ProjectId { get; set; }
    public required string Title { get; set; }
    public TaskItemStatus Status { get; set; } = TaskItemStatus.Todo;
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow;

    // Topic 10: optional deadline (UTC). Nullable: not every task has one (Topic 9's DueDate column, now from C#).
    public DateTime? DueDate { get; set; }
}
