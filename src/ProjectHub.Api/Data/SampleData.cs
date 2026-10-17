using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Data;

public static class SampleData
{
    // Returns a NEW list every call, so one caller's changes never leak into another's data.
    // Used by InMemoryProjectService and, since Topic 10, as the database seed (ProjectHubDbContext.HasData).
    // All values are FIXED (no DateTime.UtcNow): seed data is compared between migrations, so it must not change by itself.
    public static List<Project> CreateProjects()
    {
        var day = new DateTime(2026, 9, 1, 9, 0, 0, DateTimeKind.Utc);
        // Due dates as in Topic 9's sql/06: tasks 2, 5, 7 overdue; 1, 4 past but Done; 3 in 2027; 6 none.
        static DateTime Due(int month, int dayOfMonth) => new(2026, month, dayOfMonth, 17, 0, 0, DateTimeKind.Utc);

        return
        [
            new Project
            {
                Id = 1,
                Name = "Website redesign",
                Description = "New marketing site",
                CreatedAt = day,
                Tasks =
                [
                    new TaskItem { Id = 1, ProjectId = 1, Title = "Design mockups", Status = TaskItemStatus.Done, CreatedAt = day.AddDays(1), DueDate = Due(9, 10) },
                    new TaskItem { Id = 2, ProjectId = 1, Title = "Build landing page", Status = TaskItemStatus.InProgress, CreatedAt = day.AddDays(3), DueDate = Due(10, 1) },
                    new TaskItem { Id = 3, ProjectId = 1, Title = "SEO audit", CreatedAt = day.AddDays(5), DueDate = new DateTime(2027, 1, 15, 17, 0, 0, DateTimeKind.Utc) },
                    new TaskItem { Id = 4, ProjectId = 1, Title = "Write copy", Status = TaskItemStatus.Done, CreatedAt = day.AddDays(2), DueDate = Due(9, 5) },
                ],
            },
            new Project
            {
                Id = 2,
                Name = "Mobile app",
                CreatedAt = day.AddDays(4),
                Tasks =
                [
                    new TaskItem { Id = 5, ProjectId = 2, Title = "Login screen", Status = TaskItemStatus.InProgress, CreatedAt = day.AddDays(4), DueDate = Due(9, 30) },
                    new TaskItem { Id = 6, ProjectId = 2, Title = "Push notifications", CreatedAt = day.AddDays(6) },
                    new TaskItem { Id = 7, ProjectId = 2, Title = "App store listing", CreatedAt = day.AddDays(7), DueDate = Due(10, 10) },
                ],
            },
            new Project
            {
                Id = 3,
                Name = "Internal tools",
                Description = "Admin dashboards",
                CreatedAt = day.AddDays(8),
            },
        ];
    }
}
