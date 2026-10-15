using ProjectHub.Api.Entities;
using ProjectHub.Api.Services;

namespace ProjectHub.Api.Labs;

// DEBUG LAB A (Topic 5): this file contains planted bugs ON PURPOSE.
// Don't hunt for them by reading: reproduce the symptom, then find the cause with the debugger.
// Instructions: docs/lessons/05-debugging-fundamentals.md

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
            var open = project.Tasks;
            open.RemoveAll(t => t.Status == TaskItemStatus.Done);
            result[project.Name] = open.OrderByDescending(t => t.CreatedAt).ToList();
        }

        return result;
    }

    private static int CalculatePercent(int done, int total)
    {
        if (total == 0)
        {
            return 0;
        }

        return done / total * 100;
    }

    private static string Initials(string title)
    {
        var words = title.Split(' ');
        var letters = new char[words.Length];

        for (var i = 0; i < words.Length; i++)
        {
            letters[i] = char.ToUpperInvariant(words[i][0]);
        }

        return new string(letters);
    }
}
