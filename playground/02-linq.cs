#:project ../src/ProjectHub.Api/ProjectHub.Api.csproj

// Topic 2: Collections + LINQ demo.
// Run from the repo root:  dotnet run playground/02-linq.cs
// Each section shows the TypeScript equivalent in a comment above the C#.

using ProjectHub.Api.Data;
using ProjectHub.Api.Entities;

List<Project> projects = SampleData.CreateProjects();

// ---------------------------------------------------------------------------
Section("1. SelectMany: flatten all tasks of all projects");
// TS: const allTasks = projects.flatMap(p => p.tasks);
List<TaskItem> allTasks = projects.SelectMany(p => p.Tasks).ToList();
Console.WriteLine($"{allTasks.Count} tasks in {projects.Count} projects");

// ---------------------------------------------------------------------------
Section("2. Where: filter");
// TS: allTasks.filter(t => t.status === 'InProgress')
var inProgress = allTasks.Where(t => t.Status == TaskItemStatus.InProgress);
foreach (var t in inProgress)
{
    Console.WriteLine($"#{t.Id} {t.Title}");
}

// ---------------------------------------------------------------------------
Section("3. Select: map / projection");
// TS: allTasks.map(t => t.title)
IEnumerable<string> titles = allTasks.Select(t => t.Title);
Console.WriteLine(string.Join(", ", titles));

// TS: allTasks.map(t => ({ t.id, upper: t.title.toUpperCase() }))
// 'new { ... }' is an ANONYMOUS TYPE: a compiler-generated class with read-only properties.
var shortInfo = allTasks.Select(t => new { t.Id, Upper = t.Title.ToUpper() }).Take(2);
foreach (var x in shortInfo)
{
    Console.WriteLine(x); // anonymous types print as { Id = 1, Upper = DESIGN MOCKUPS }
}

// ---------------------------------------------------------------------------
Section("4. OrderBy / ThenBy: sort (returns a NEW sequence, source untouched)");
// TS: [...allTasks].sort((a, b) => a.status - b.status || b.createdAt - a.createdAt)
var sorted = allTasks
    .OrderBy(t => t.Status)
    .ThenByDescending(t => t.CreatedAt);
foreach (var t in sorted)
{
    Console.WriteLine($"{t.Status,-10} {t.CreatedAt:yyyy-MM-dd} {t.Title}");
}

// ---------------------------------------------------------------------------
Section("5. First / FirstOrDefault / Single: find");
// TS: allTasks.find(t => t.id === 5)        -> undefined if not found
TaskItem? found = allTasks.FirstOrDefault(t => t.Id == 5);
TaskItem? missing = allTasks.FirstOrDefault(t => t.Id == 99);
Console.WriteLine($"FirstOrDefault(Id 5):  {found?.Title}");
Console.WriteLine($"FirstOrDefault(Id 99): {(missing is null ? "null" : missing.Title)}");

// First() throws when nothing matches. Single() throws when there is not EXACTLY one match.
Try("First(Id 99)", () => allTasks.First(t => t.Id == 99).Title);
Try("Single(Status Done)", () => allTasks.Single(t => t.Status == TaskItemStatus.Done).Title);

// ---------------------------------------------------------------------------
Section("6. Any / All / Count / Contains: some / every / length / includes");
// TS: tasks.some(...), tasks.every(...), tasks.filter(...).length
Console.WriteLine($"Any task Done?              {allTasks.Any(t => t.Status == TaskItemStatus.Done)}");
Console.WriteLine($"All tasks have a title?     {allTasks.All(t => t.Title.Length > 0)}");
Console.WriteLine($"Count of Todo:              {allTasks.Count(t => t.Status == TaskItemStatus.Todo)}");
Console.WriteLine($"Titles contain 'SEO audit'? {titles.Contains("SEO audit")}");

var empty = projects.Single(p => p.Id == 3);
// Gotcha: All() on an EMPTY collection is true (nothing violates the rule). Same as JS [].every(...).
Console.WriteLine($"Empty project: all tasks Done? {empty.Tasks.All(t => t.Status == TaskItemStatus.Done)}");

// ---------------------------------------------------------------------------
Section("7. GroupBy: group tasks by status");
// TS: Object.groupBy(allTasks, t => t.status)   (or a reduce into a Map)
var byStatus = allTasks.GroupBy(t => t.Status);
foreach (var group in byStatus)
{
    // A group is an IGrouping<TKey, TElement>: it has a .Key AND is itself a sequence of tasks.
    Console.WriteLine($"{group.Key}: {group.Count()} -> {string.Join(", ", group.Select(t => t.Title))}");
}

// ---------------------------------------------------------------------------
Section("8. Projection into a record (a DTO shape)");
// TS: projects.map(p => ({ id: p.id, name: p.name, taskCount: p.tasks.length, ... }))
List<ProjectSummary> summaries = projects
    .Select(p => new ProjectSummary(
        p.Id,
        p.Name,
        TaskCount: p.Tasks.Count,
        DoneCount: p.Tasks.Count(t => t.Status == TaskItemStatus.Done)))
    .OrderByDescending(s => s.TaskCount)
    .ToList();
summaries.ForEach(Console.WriteLine);

// ---------------------------------------------------------------------------
Section("9. Aggregates: Sum / Max / Average / MaxBy / Aggregate (reduce)");
// TS: tasks.length, Math.max(...), tasks.reduce((acc, t) => ..., seed)
Console.WriteLine($"Total tasks (Sum):   {projects.Sum(p => p.Tasks.Count)}");
Console.WriteLine($"Newest task (Max):   {allTasks.Max(t => t.CreatedAt):yyyy-MM-dd}");
Console.WriteLine($"Avg tasks/project:   {projects.Average(p => p.Tasks.Count):0.00}");
Console.WriteLine($"MaxBy (whole item):  {allTasks.MaxBy(t => t.CreatedAt)!.Title}");
string titleLine = allTasks.Aggregate("", (acc, t) => acc.Length == 0 ? t.Title : acc + " | " + t.Title);
Console.WriteLine($"Aggregate (reduce):  {titleLine}");

// Gotcha: Max() on an EMPTY sequence of a value type throws. JS Math.max() would give -Infinity.
Try("Max on empty project", () => empty.Tasks.Max(t => t.CreatedAt).ToString("yyyy-MM-dd"));

// ---------------------------------------------------------------------------
Section("10. Dictionary<TKey, TValue>: fast lookup by key (TS: Map)");
// TS: const byId = new Map(projects.map(p => [p.id, p]));
Dictionary<int, Project> projectsById = projects.ToDictionary(p => p.Id);
Console.WriteLine($"projectsById[2].Name = {projectsById[2].Name}");

// TS: byId.get(42) ?? 'not found'.  C# indexer [42] would THROW KeyNotFoundException, so use TryGetValue.
if (projectsById.TryGetValue(42, out Project? p42))
{
    Console.WriteLine(p42.Name);
}
else
{
    Console.WriteLine("TryGetValue(42): not found");
}
Try("projectsById[42]", () => projectsById[42].Name);

// Dictionary from a GroupBy: status -> count
Dictionary<TaskItemStatus, int> countByStatus = allTasks
    .GroupBy(t => t.Status)
    .ToDictionary(g => g.Key, g => g.Count());
foreach (var (status, count) in countByStatus)
{
    Console.WriteLine($"{status} = {count}");
}

// ---------------------------------------------------------------------------
Section("11. Deferred execution: a query is a RECIPE, not a result");
var source = new List<int> { 1, 2, 3 };
int evaluations = 0;
IEnumerable<int> query = source.Where(n => { evaluations++; return n > 1; });
Console.WriteLine($"After defining the query: evaluations = {evaluations}  (nothing ran yet)");

source.Add(4); // change the source AFTER defining the query
Console.WriteLine($"First enumeration:  [{string.Join(", ", query)}]   (sees the added 4!)");
Console.WriteLine($"Second enumeration: [{string.Join(", ", query)}]   (runs the filter AGAIN)");
Console.WriteLine($"evaluations = {evaluations}  (4 items x 2 enumerations)");

List<int> snapshot = query.ToList(); // ToList() runs the query ONCE and stores the result
source.Add(5);
Console.WriteLine($"snapshot after adding 5: [{string.Join(", ", snapshot)}]  (frozen)");

// ---------------------------------------------------------------------------
Section("12. Query syntax (same thing, SQL-like spelling)");
var querySyntax =
    from t in allTasks
    where t.Status != TaskItemStatus.Done
    orderby t.Title
    select t.Title;
Console.WriteLine(string.Join(", ", querySyntax));

// ---------------------------------------------------------------------------
Section("13. Paging: Skip / Take (what an API list endpoint does)");
// TS: allTasks.slice(page * size, page * size + size)
int page = 1, size = 3; // page index starts at 0
var pageItems = allTasks.OrderBy(t => t.Id).Skip(page * size).Take(size);
Console.WriteLine($"Page {page}: {string.Join(", ", pageItems.Select(t => $"#{t.Id}"))}");

// ===========================================================================
// helpers
static void Section(string title) => Console.WriteLine($"\n=== {title} ===");

static void Try(string label, Func<string> action)
{
    try
    {
        Console.WriteLine($"{label}: {action()}");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"{label}: THROWS {ex.GetType().Name}: {ex.Message}");
    }
}

record ProjectSummary(int Id, string Name, int TaskCount, int DoneCount);
