namespace ProjectHub.Api.Entities;

public class Project
{
    public int Id { get; set; }
    public required string Name { get; set; }
    public string? Description { get; set; }
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow;
    public List<TaskItem> Tasks { get; set; } = [];
}
