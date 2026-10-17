#:project ../src/ProjectHub.Api/ProjectHub.Api.csproj

// Topic 4: async/await demo.
// Run from the repo root:  dotnet run --no-cache playground/04-async.cs
// Timings in the output are approximate and depend on your machine.

using System.Diagnostics;
using ProjectHub.Api.Data;
using ProjectHub.Api.Exceptions;
using ProjectHub.Api.Services;

// Every "database call" in this service waits 300 ms, like a real network + SQL round-trip.
IProjectService service = new InMemoryProjectService(SampleData.CreateProjects(), TimeSpan.FromMilliseconds(300));

// ---------------------------------------------------------------------------
Section("1. Task<T> is a Promise<T>; await unwraps it");
// TS: const promise: Promise<Project | null> = service.getById(1);
Task<ProjectHub.Api.Entities.Project?> task = service.GetByIdAsync(1);
Console.WriteLine($"Right after the call: IsCompleted = {task.IsCompleted}   (still 'pending')");
var project = await task; // TS: const project = await promise;
Console.WriteLine($"After await:          IsCompleted = {task.IsCompleted}, project = {project?.Name}");

// ---------------------------------------------------------------------------
Section("2. Sequential awaits vs Task.WhenAll (Promise.all)");
var sw = Stopwatch.StartNew();
var p1 = await service.GetByIdAsync(1);
var p2 = await service.GetByIdAsync(2);
var p3 = await service.GetByIdAsync(3);
Console.WriteLine($"Sequential: {sw.ElapsedMilliseconds,5} ms  (3 x 300 ms, one after another)");

sw.Restart();
// Start all three FIRST, then wait for all of them. TS: await Promise.all([a, b, c])
var all = await Task.WhenAll(service.GetByIdAsync(1), service.GetByIdAsync(2), service.GetByIdAsync(3));
Console.WriteLine($"WhenAll:    {sw.ElapsedMilliseconds,5} ms  (the three waits overlap)  -> {string.Join(", ", all.Select(p => p?.Name))}");

// ---------------------------------------------------------------------------
Section("3. Threads: the code after an await may continue on ANOTHER thread");
var threadIds = new List<int> { Environment.CurrentManagedThreadId };
for (var i = 0; i < 8; i++)
{
    await Task.Delay(50);                              // while waiting, NO thread is blocked
    threadIds.Add(Environment.CurrentManagedThreadId); // whichever pool thread was free continues here
}
Console.WriteLine($"Thread id before the first await, then after each of 8 awaits: {string.Join(" -> ", threadIds)}");
Console.WriteLine("Same or different ids: any free thread-pool thread can continue the method (JS always has one thread).");

// ---------------------------------------------------------------------------
Section("4. Why backend I/O must be awaited: blocking vs non-blocking");
// 50 "requests", each waiting 500 ms for I/O. The machine has a limited number of thread-pool threads.
const int requests = 50;
sw.Restart();
await Task.WhenAll(Enumerable.Range(0, requests).Select(_ => Task.Run(() => Thread.Sleep(500))));
Console.WriteLine($"Blocking  (Thread.Sleep):      {sw.ElapsedMilliseconds,6} ms  (each request HOLDS a thread while waiting)");

sw.Restart();
await Task.WhenAll(Enumerable.Range(0, requests).Select(_ => Task.Delay(500)));
Console.WriteLine($"Async     (await Task.Delay):  {sw.ElapsedMilliseconds,6} ms  (no thread is held while waiting)");
Console.WriteLine($"Processor count: {Environment.ProcessorCount}  (the pool starts with about this many threads and grows slowly)");

// ---------------------------------------------------------------------------
Section("5. CancellationToken: stop work nobody needs any more (AbortController)");
// TS: const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 100); fetch(url, { signal: ctrl.signal })
using (var cts = new CancellationTokenSource())
{
    cts.CancelAfter(TimeSpan.FromMilliseconds(100));
    sw.Restart();
    try
    {
        await service.GetAllAsync(cts.Token); // would take 300 ms
        Console.WriteLine("finished (not expected)");
    }
    catch (OperationCanceledException ex)
    {
        Console.WriteLine($"Cancelled after {sw.ElapsedMilliseconds} ms: {ex.GetType().Name}");
    }
}

// An already-cancelled token: the call gives up immediately, before doing any work.
using (var cancelled = new CancellationTokenSource())
{
    cancelled.Cancel();
    try
    {
        await service.CreateAsync("Never created", null, cancelled.Token);
    }
    catch (OperationCanceledException)
    {
        var exists = (await service.GetAllAsync()).Any(p => p.Name == "Never created");
        Console.WriteLine($"Create with a cancelled token -> OperationCanceledException; project exists? {exists}");
    }
}

// ---------------------------------------------------------------------------
Section("6. Exceptions travel inside the Task until you await it");
Task<ProjectHub.Api.Entities.Project> failing = service.CreateAsync("Mobile app", null); // duplicate name
Console.WriteLine($"Called CreateAsync without await: no exception yet. Status = {failing.Status}");
try
{
    await failing; // the exception is re-thrown HERE, like a rejected promise in try/await
}
catch (BusinessRuleException ex)
{
    Console.WriteLine($"Thrown at the await: {ex.Message}   (Status was {failing.Status})");
}

// ---------------------------------------------------------------------------
Section("7. Shared state + concurrency: why ProjectService uses lock");
// Unlike JS (one thread), these 5 calls really run in parallel on different threads after their awaits.
var sameName = await Task.WhenAll(Enumerable.Range(0, 5).Select(async _ =>
{
    try
    {
        await service.CreateAsync("Race project", null);
        return "created";
    }
    catch (BusinessRuleException)
    {
        return "rejected";
    }
}));
Console.WriteLine($"5 concurrent creates with the SAME name: {string.Join(", ", sameName)}");

var created = await Task.WhenAll(Enumerable.Range(1, 20).Select(i => service.CreateAsync($"Parallel {i}", null)));
var ids = created.Select(p => p.Id).ToList();
Console.WriteLine($"20 concurrent creates: {ids.Count} projects, {ids.Distinct().Count()} distinct ids");

// ---------------------------------------------------------------------------
Section("8. Pitfall: .Result blocks the thread (sync-over-async)");
sw.Restart();
var blocked = service.GetByIdAsync(2).Result; // works here, but this thread is stuck for the whole 300 ms
Console.WriteLine($".Result returned '{blocked?.Name}' after {sw.ElapsedMilliseconds} ms, with the thread blocked the whole time");
Console.WriteLine("In ASP.NET Core: use 'await' instead. .Result/.Wait() waste threads (and deadlock in some older app types).");

// ===========================================================================
static void Section(string title) => Console.WriteLine($"\n=== {title} ===");
