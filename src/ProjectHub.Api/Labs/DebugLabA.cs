using ProjectHub.Api.Data;
using ProjectHub.Api.Entities;
using ProjectHub.Api.Services;

namespace ProjectHub.Api.Labs;

// DEBUG LAB A (Topic 5): reproduces three bug reports (DashboardReport had the bugs; they are fixed now).
// Start it with the debugger by temporarily adding this line to Program.cs, right before app.Run():
//     await ProjectHub.Api.Labs.DebugLabA.RunAsync();
public static class DebugLabA
{
    public static async Task RunAsync()
    {
        var service = new InMemoryProjectService(CreateLabData());
        var report = new DashboardReport(service);

        Console.WriteLine("=== Bug report 1: 'The progress widget shows 0% for projects that are half done' ===");
        foreach (var progress in await report.GetProgressAsync())
        {
            Console.WriteLine($"  {progress.Name,-18} {progress.DoneTasks,3}/{progress.TotalTasks,-3} done -> {progress.PercentDone}%");
        }

        Console.WriteLine();
        Console.WriteLine("=== Bug report 2: 'The task codes widget fails to load' ===");
        try
        {
            var codes = await report.GetTaskCodesAsync();
            Console.WriteLine($"  {codes.Count} codes, first: {codes[0]}, task 158: {codes.Single(c => c.EndsWith("-158"))}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  FAILED: {ex.GetType().Name}: {ex.Message}");
        }

        Console.WriteLine();
        Console.WriteLine("=== Bug report 3: 'After the Open work widget loads, done tasks vanish from the project page' ===");
        var before = (await service.GetByIdAsync(1))!.Tasks.Count;
        await report.GetOpenWorkAsync();
        var after = (await service.GetByIdAsync(1))!.Tasks.Count;
        Console.WriteLine($"  Project 1 task count before the widget: {before}, after: {after}");
    }

    // The sample data plus a big imported project, like real production data.
    private static List<Project> CreateLabData()
    {
        var projects = SampleData.CreateProjects();
        var imported = new Project
        {
            Id = 4,
            Name = "Legacy import",
            Description = "Tasks migrated from the old tracker",
            CreatedAt = new DateTime(2026, 9, 10, 9, 0, 0, DateTimeKind.Utc),
        };

        string[] verbs = ["Review", "Migrate", "Archive", "Check", "Update"];
        string[] things = ["user table", "invoice export", "login flow", "email template", "audit log", "search index"];

        for (var i = 0; i < 300; i++)
        {
            var title = $"{verbs[i % verbs.Length]} {things[i % things.Length]}";
            if (i == 150)
            {
                title = "Migrate  legacy reports"; // copied from the old tracker as-is
            }

            imported.Tasks.Add(new TaskItem
            {
                Id = 8 + i,
                ProjectId = imported.Id,
                Title = title,
                Status = i % 3 == 0 ? TaskItemStatus.Done : TaskItemStatus.Todo,
                CreatedAt = imported.CreatedAt.AddMinutes(i),
            });
        }

        projects.Add(imported);
        return projects;
    }
}
