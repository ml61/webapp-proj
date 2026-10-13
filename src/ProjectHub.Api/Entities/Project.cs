namespace ProjectHub.Api.Entities;

public class Project    
{
    public int Id { get; set; }                      // property: get/set accessors
    public required string Name { get; set; }        // 'required': must be set when creating the object
    public string? Description { get; set; }         // optional
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow; // 'init': settable only during creation
    public List<TaskItem> Tasks { get; set; } = []; // collection expression (like `= []`)
}