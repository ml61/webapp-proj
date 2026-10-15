#:project ../src/ProjectHub.Api/ProjectHub.Api.csproj

// Topic 3: Interfaces, generics, exceptions demo.
// (Updated in Topic 4: the service is async now, so calls use await and the ...Async names.)
// Run from the repo root:  dotnet run --no-cache playground/03-services-exceptions.cs

using ProjectHub.Api.Data;
using ProjectHub.Api.Entities;
using ProjectHub.Api.Exceptions;
using ProjectHub.Api.Services;

// ---------------------------------------------------------------------------
Section("1. Program against the INTERFACE, not the class");
// The variable type is the interface; the object is one concrete implementation.
// TS: const service: IProjectService = new ProjectService(data);
IProjectService service = new ProjectService(SampleData.CreateProjects());

Console.WriteLine($"GetAll: {(await service.GetAllAsync()).Count} projects");
Console.WriteLine($"GetById(1):  {(await service.GetByIdAsync(1))?.Name}");
Console.WriteLine($"GetById(99): {(await service.GetByIdAsync(99))?.Name ?? "null (not found is a normal answer)"}");

// ---------------------------------------------------------------------------
Section("2. Happy path: Create + AddTask");
Project created = await service.CreateAsync("  Docs portal  ", "Public API docs");
Console.WriteLine($"Created #{created.Id} '{created.Name}' (name was trimmed)");
TaskItem task = await service.AddTaskAsync(created.Id, "Write getting started");
Console.WriteLine($"Added task #{task.Id} '{task.Title}' to project #{task.ProjectId}, status {task.Status}");

// ---------------------------------------------------------------------------
Section("3. The business rule: expected errors -> BusinessRuleException");
await TryCreate(service, "WEBSITE REDESIGN");   // duplicate, different case
await TryCreate(service, "   ");             // empty after trim
await TryCreate(service, new string('x', 101)); // too long

// ---------------------------------------------------------------------------
Section("4. NotFoundException carries data, not only a message");
try
{
    await service.AddTaskAsync(projectId: 42, title: "Ghost task");
}
catch (NotFoundException ex)
{
    Console.WriteLine($"Message:    {ex.Message}");
    Console.WriteLine($"EntityName: {ex.EntityName}, Key: {ex.Key}");
}

// ---------------------------------------------------------------------------
Section("5. catch order, 'when' filters, finally");
foreach (var projectId in new[] { 1, 42 })
{
    try
    {
        // Project 1 exists -> the empty title fails. Project 42 does not -> a valid title, but NotFound.
        var title = projectId == 1 ? "" : "Valid title";
        Console.WriteLine($"AddTask({projectId}, \"{title}\") ...");
        await service.AddTaskAsync(projectId, title);
    }
    catch (NotFoundException ex) when (ex.Key is int id && id > 10)
    {
        // 'when' = only catch if the condition is true; otherwise the exception keeps flying.
        Console.WriteLine($"  caught NotFoundException for a big id: {ex.Message}");
    }
    catch (BusinessRuleException ex)
    {
        Console.WriteLine($"  caught BusinessRuleException: {ex.Message}");
    }
    catch (Exception ex)
    {
        // Most general LAST. Putting it first would be a compile error (later catches unreachable).
        Console.WriteLine($"  caught something unexpected: {ex.GetType().Name}");
    }
    finally
    {
        // Runs ALWAYS: success, caught exception, or an exception that keeps flying.
        Console.WriteLine("  finally: runs no matter what");
    }
}

// ---------------------------------------------------------------------------
Section("6. throw; vs throw ex;  (stack trace)");
foreach (var useThrowEx in new[] { false, true })
{
    try
    {
        Rethrow(useThrowEx);
    }
    catch (Exception ex)
    {
        // First line of the stack trace, without the file path: "at ...ThrowDeepInside()" or "at ...Rethrow(...)"
        var where = ex.StackTrace!.Split('\n')[0].Trim().Split(" in ")[0];
        Console.WriteLine($"{(useThrowEx ? "throw ex;" : "throw;   ")} -> top frame: {where}");
    }
}

// ---------------------------------------------------------------------------
Section("7. Polymorphism: a different implementation behind the same interface");
// LoggingProjectService wraps ANY IProjectService and adds logging (the Decorator pattern).
// The calling code below does not change at all: it only knows IProjectService.
IProjectService logged = new LoggingProjectService(new ProjectService(SampleData.CreateProjects()));
await PrintProjectCount(logged);
await TryCreate(logged, "Mobile app");

// ---------------------------------------------------------------------------
Section("8. Encapsulation: GetAll() returns a READ-ONLY list");
IReadOnlyList<Project> all = await service.GetAllAsync();
// all.Add(...)  -> compile error: IReadOnlyList has no Add.
// Even casting back to a writable interface fails at runtime:
try
{
    ((IList<Project>)all).Add(new Project { Name = "Sneaky" });
}
catch (NotSupportedException ex)
{
    Console.WriteLine($"Cast + Add: {ex.GetType().Name}: {ex.Message}");
}
// But the PROJECTS inside are still mutable entities: a caller can change them.
all[0].Name = "Renamed by a caller!";
Console.WriteLine($"service.GetById(1).Name = {(await service.GetByIdAsync(1))!.Name}   <- leak (DTOs fix this in Topic 6)");

// ---------------------------------------------------------------------------
Section("9. Generics: our own generic method with a constraint");
// TS: function largest<T extends Comparable<T>>(items: T[]): T
Console.WriteLine($"Largest(int):      {Largest(new[] { 3, 9, 4 })}");
Console.WriteLine($"Largest(string):   {Largest(new[] { "pear", "apple", "zebra" })}");
Console.WriteLine($"Largest(DateTime): {Largest((await service.GetAllAsync()).Select(p => p.CreatedAt)):yyyy-MM-dd}");
// Largest(await service.GetAllAsync());  -> compile error: Project does not implement IComparable<Project>

// ---------------------------------------------------------------------------
Section("10. Generics: our own generic type");
// One definition, many types. TS: type Page<T> = { items: T[]; pageNumber: number; totalCount: number }
Page<string> namesPage = ToPage((await service.GetAllAsync()).Select(p => p.Name), pageNumber: 1, pageSize: 2);
Page<TaskItem> tasksPage = ToPage((await service.GetAllAsync()).SelectMany(p => p.Tasks), pageNumber: 2, pageSize: 3);
Console.WriteLine($"Page<string>:   page {namesPage.PageNumber}, {namesPage.Items.Count} of {namesPage.TotalCount}: {string.Join(", ", namesPage.Items)}");
Console.WriteLine($"Page<TaskItem>: page {tasksPage.PageNumber}, {tasksPage.Items.Count} of {tasksPage.TotalCount}: {string.Join(", ", tasksPage.Items.Select(t => $"#{t.Id}"))}");

// ===========================================================================
// helpers

static void Section(string title) => Console.WriteLine($"\n=== {title} ===");

static async Task TryCreate(IProjectService service, string name)
{
    var label = name.Length > 20 ? name[..20] + "..." : $"'{name}'";
    try
    {
        var project = await service.CreateAsync(name, null);
        Console.WriteLine($"Create({label}): OK #{project.Id}");
    }
    catch (BusinessRuleException ex)
    {
        // Expected error: we know what it means and what to tell the user.
        Console.WriteLine($"Create({label}): rejected -> {ex.Message}");
    }
}

static async Task PrintProjectCount(IProjectService service) =>
    Console.WriteLine($"PrintProjectCount: {(await service.GetAllAsync()).Count} projects");

static void Rethrow(bool useThrowEx)
{
    try
    {
        ThrowDeepInside();
    }
    catch (Exception ex)
    {
        if (useThrowEx)
        {
#pragma warning disable CA2200 // on purpose: shows why 'throw ex;' is wrong
            throw ex;   // resets the stack trace: the original location is LOST
#pragma warning restore CA2200
        }
        throw;          // rethrows the same exception, stack trace preserved
    }
}

static void ThrowDeepInside() => throw new InvalidOperationException("boom");

// Generic method: T is chosen by the caller (usually inferred). The constraint guarantees CompareTo exists.
static T Largest<T>(IEnumerable<T> items) where T : IComparable<T>
{
    using var e = items.GetEnumerator();
    if (!e.MoveNext())
    {
        throw new ArgumentException("Sequence is empty.", nameof(items));
    }

    var largest = e.Current;
    while (e.MoveNext())
    {
        if (e.Current.CompareTo(largest) > 0)
        {
            largest = e.Current;
        }
    }
    return largest;
}

static Page<T> ToPage<T>(IEnumerable<T> source, int pageNumber, int pageSize)
{
    var list = source.ToList(); // enumerate ONCE (Topic 2: avoid multiple enumeration)
    var items = list.Skip((pageNumber - 1) * pageSize).Take(pageSize).ToList();
    return new Page<T>(items, pageNumber, list.Count);
}

// Generic record: a typed "page of results" (an API list endpoint will return this shape).
record Page<T>(IReadOnlyList<T> Items, int PageNumber, int TotalCount);

// A second implementation of the same interface: wraps another one and logs every call.
class LoggingProjectService(IProjectService inner) : IProjectService
{
    public Task<IReadOnlyList<Project>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        Console.WriteLine("  [log] GetAll()");
        return inner.GetAllAsync(cancellationToken);
    }

    public Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        Console.WriteLine($"  [log] GetById({id})");
        return inner.GetByIdAsync(id, cancellationToken);
    }

    public async Task<Project> CreateAsync(string name, string? description, CancellationToken cancellationToken = default)
    {
        Console.WriteLine($"  [log] Create('{name}')");
        try
        {
            return await inner.CreateAsync(name, description, cancellationToken);
        }
        catch (BusinessRuleException ex)
        {
            Console.WriteLine($"  [log] Create failed: {ex.Message}");
            throw; // log and rethrow: the caller still decides what to do
        }
    }

    public Task<TaskItem> AddTaskAsync(int projectId, string title, CancellationToken cancellationToken = default)
    {
        Console.WriteLine($"  [log] AddTask({projectId}, '{title}')");
        return inner.AddTaskAsync(projectId, title, cancellationToken);
    }
}
