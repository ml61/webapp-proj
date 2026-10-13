using ProjectHub.Api.Entities;

namespace ProjectHub.Api.Data;

public static class SampleData
{
    // Returns a NEW list every call, so one caller's changes never leak into another's data.
    public static List<Project> CreateProjects()
    {
        var day = new DateTime(2026, 9, 1, 9, 0, 0, DateTimeKind.Utc);

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
                    new TaskItem { Id = 1, ProjectId = 1, Title = "Design mockups", Status = TaskItemStatus.Done, CreatedAt = day.AddDays(1) },
                    new TaskItem { Id = 2, ProjectId = 1, Title = "Build landing page", Status = TaskItemStatus.InProgress, CreatedAt = day.AddDays(3) },
                    new TaskItem { Id = 3, ProjectId = 1, Title = "SEO audit", CreatedAt = day.AddDays(5) },
                    new TaskItem { Id = 4, ProjectId = 1, Title = "Write copy", Status = TaskItemStatus.Done, CreatedAt = day.AddDays(2) },
                ],
            },
            new Project
            {
                Id = 2,
                Name = "Mobile app",
                CreatedAt = day.AddDays(4),
                Tasks =
                [
                    new TaskItem { Id = 5, ProjectId = 2, Title = "Login screen", Status = TaskItemStatus.InProgress, CreatedAt = day.AddDays(4) },
                    new TaskItem { Id = 6, ProjectId = 2, Title = "Push notifications", CreatedAt = day.AddDays(6) },
                    new TaskItem { Id = 7, ProjectId = 2, Title = "App store listing", CreatedAt = day.AddDays(7) },
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
