namespace ProjectHub.Api.Entities;

public enum TaskItemStatus { ToDo, InProgress, Done }
public class TaskItem 
{
    public int Id { get; set; }
    public required string Title { get; set; }
    public int ProjectId { get; set; }
    public TaskItemStatus Status { get; set; } =  TaskItemStatus.ToDo;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
