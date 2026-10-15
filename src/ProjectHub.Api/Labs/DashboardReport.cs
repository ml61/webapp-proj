using ProjectHub.Api.Entities;
using ProjectHub.Api.Services;

namespace ProjectHub.Api.Labs;

// DEBUG LAB A (Topic 5): this file had 3 planted bugs. They are FIXED now; each fix is marked "LAB FIX".
// Instructions and the debugging walkthrough: docs/lessons/05-debugging-fundamentals.md

public record ProjectProgress(int ProjectId, string Name, int DoneTasks, int TotalTasks, int PercentDone);

// Builds the numbers for a (future) dashboard page.
public class DashboardReport(IProjectService projects)
{
    // "Progress" widget: how much of each project is done.
    public async Task<List<ProjectProgress>> GetProgressAsync(CancellationToken cancellationToken = default)
    {
        var all = await projects.GetAllAsync(cancellationToken);
        var result = new List<ProjectProgress>();

        foreach (var project in all)
        {
            var done = project.Tasks.Count(t => t.Status == TaskItemStatus.Done);
            var total = project.Tasks.Count;
            result.Add(new ProjectProgress(project.Id, project.Name, done, total, CalculatePercent(done, total)));
        }

        return result;
    }

    // "Task codes" widget: a short code per task, e.g. "Design mockups" (#1) -> "DM-1".
    public async Task<List<string>> GetTaskCodesAsync(CancellationToken cancellationToken = default)
    {
        var all = await projects.GetAllAsync(cancellationToken);
        var codes = new List<string>();

        foreach (var project in all)
        {
            foreach (var task in project.Tasks)
            {
                codes.Add($"{Initials(task.Title)}-{task.Id}");
            }
        }

        return codes;
    }

    // "Open work" widget: the open (not done) tasks of each project, newest first.
    public async Task<Dictionary<string, List<TaskItem>>> GetOpenWorkAsync(CancellationToken cancellationToken = default)
    {
        var all = await projects.GetAllAsync(cancellationToken);
        var result = new Dictionary<string, List<TaskItem>>();

        foreach (var project in all)
        {
            // LAB FIX (bug 3): was `var open = project.Tasks; open.RemoveAll(...)`. That copied the REFERENCE,
            // so RemoveAll deleted tasks from the service's real list. Where() builds a new sequence instead.
            result[project.Name] = project.Tasks
                .Where(t => t.Status != TaskItemStatus.Done)
                .OrderByDescending(t => t.CreatedAt)
                .ToList();
        }

        return result;
    }

    private static int CalculatePercent(int done, int total)
    {
        if (total == 0)
        {
            return 0;
        }

        // LAB FIX (bug 1): was `done / total * 100`. int / int is integer division (2 / 4 == 0).
        // 100.0 makes it double math; AwayFromZero rounds 12.5 up to 13 (the default would give 12).
        return (int)Math.Round(done * 100.0 / total, MidpointRounding.AwayFromZero);
    }

    private static string Initials(string title)
    {
        // LAB FIX (bug 2): was `title.Split(' ')`. A double space produced an empty word, and ""[0] threw
        // IndexOutOfRangeException. Imported data does not pass through the service's validation.
        var words = title.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return words.Length == 0
            ? "?"
            : string.Concat(words.Select(w => char.ToUpperInvariant(w[0])));
    }
}
