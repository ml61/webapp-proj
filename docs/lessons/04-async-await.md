# Lesson 4: Async/await

**Roadmap:** Week 1, Topic 4. **Time:** about 2–3 h.
**Checkpoint:** you can explain **why backend I/O should be awaited**, and the service passes a `CancellationToken` through.

**Files for this lesson:**
- `src/ProjectHub.Api/Services/IProjectService.cs`: now async (`...Async` methods returning `Task<T>`, each takes a `CancellationToken`)
- `src/ProjectHub.Api/Services/ProjectService.cs`: async, simulated database latency, `lock` for thread safety
- `playground/04-async.cs`: runnable demo with 8 sections. Run it from the repo root with `dotnet run playground/04-async.cs`.
- `playground/03-services-exceptions.cs`: updated to the async API, with the same lessons as before

---

## 1. The mapping you already know

| TypeScript / JS | C# | Note |
|---|---|---|
| `Promise<T>` | `Task<T>` | a value that will be available later |
| `Promise<void>` | `Task` | no result, just "done" (or failed) |
| `async function f(): Promise<T>` | `async Task<T> FAsync()` | by convention the name **ends with `Async`** |
| `await p` | `await t` | unwraps the result, or re-throws the error |
| `Promise.all([a, b])` | `Task.WhenAll(a, b)` | wait for all |
| `Promise.race([a, b])` | `Task.WhenAny(a, b)` | first one to finish |
| `Promise.resolve(x)` | `Task.FromResult(x)` | an already-completed task |
| `new Promise(r => setTimeout(r, 300))` | `Task.Delay(300)` | wait without blocking |
| `AbortController` | `CancellationTokenSource` | the side that **cancels** |
| `AbortSignal` | `CancellationToken` | the side you **pass around** and check |
| rejected promise | faulted task | the exception is stored in the task until awaited |

The syntax is almost identical. **The difference is threads.**

## 2. The big difference: JS has one thread, .NET has a thread pool

- **JS / Node:** one thread plus an event loop. After an `await`, your code continues on *the same* single thread, and two pieces of your code never run at the same moment.
- **.NET:** a **thread pool**, a set of worker threads (it starts at about one per CPU core and grows slowly). An ASP.NET Core request runs on one of these threads. At an `await` on real I/O:
  1. the method **pauses** and **returns its thread to the pool** (the thread is now free for other requests),
  2. when the I/O completes, **any free pool thread** picks up the rest of the method.

Demo section 3: the thread id changes between awaits (`7 -> 8 -> 8 -> 7 ...`).

Consequence: code after awaits **can really run in parallel** on several threads. Shared mutable state (like our `List<Project>`) needs protection. That's why `ProjectService` now uses `lock` (section 5).

## 3. Why backend I/O must be awaited (the checkpoint answer)

A web server handles many requests at once with a **limited number of threads**. Most of a typical request's time is spent **waiting**: for the database, another HTTP API, a file.

- **Blocking wait** (`Thread.Sleep`, `.Result`, `.Wait()`, synchronous DB calls): the thread **sits there doing nothing** but can't serve anyone else. With many requests, all threads end up blocked, new requests queue up, latency explodes, and you get timeouts. This is **thread-pool starvation**.
- **`await`**: while waiting, the thread goes back to the pool and serves other requests. Few threads can handle thousands of concurrent requests that are mostly waiting.

Demo section 4 (50 requests, each waiting 500 ms, on a 4-core machine):
```
Blocking  (Thread.Sleep):        5511 ms   <- each request HOLDS a thread; the pool grows slowly
Async     (await Task.Delay):     501 ms   <- no thread held while waiting
```
One-sentence answer: **awaiting I/O frees the thread while waiting, so the server handles more concurrent requests with the same threads. Blocking holds threads idle and leads to thread-pool starvation.**

What async is **not**:
- It doesn't make a single request faster. A 300 ms query still takes 300 ms.
- It doesn't help **CPU-bound** work (heavy calculations). There's no waiting to give back. In ASP.NET you just run that code. `Task.Run` moves work to another pool thread, which doesn't help a server.
- **Async all the way:** once one method is async, its callers should `await` it too, up to the controller. Mixing in `.Result` brings the blocking back.

## 4. Writing async methods

```csharp
public async Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
{
    await SimulateDatabaseCallAsync(cancellationToken); // pause here, thread returns to the pool
    lock (_gate)
    {
        return FindById(id);                            // return a Project?, the compiler wraps it in Task<Project?>
    }
}
```
- `async` lets you use `await` inside, and makes the compiler **wrap the return value** in a `Task<T>`. You `return project;`, not `return Task.FromResult(project);`.
- Under the hood the compiler turns the method into a **state machine** that can pause and resume. TS does the same with generators.
- **Return type options:** `Task<T>` (result), `Task` (no result), `ValueTask<T>` (an optimization for hot paths that often complete synchronously: recognize it, don't use it by default), and `async void` (**only** for event handlers, see pitfalls).
- **A method without `async` can still return a Task.** `LoggingProjectService.GetAllAsync` in the Topic 3 demo just returns `inner.GetAllAsync(...)`: it passes the task through without awaiting. That's fine when there's nothing to do afterwards.

### Exceptions in async code (demo section 6)
An exception thrown inside an async method is **stored in the Task** (status `Faulted`). It's re-thrown **at the `await`**, so `try { await x; } catch` works exactly like in JS. If you never await a task, its exception is silently lost. That's the C# version of an unhandled promise rejection.

## 5. CancellationToken (AbortController)

**Why a backend needs it:** a user closes the tab, or a client times out after 5 s, but the server keeps running a 30 s query for nobody. ASP.NET Core gives every request a token that is **cancelled when the client disconnects** (`HttpContext.RequestAborted`; in a controller you just add a `CancellationToken` parameter, Topic 6). Passing it down to EF Core makes the database query stop too.

```csharp
using var cts = new CancellationTokenSource();          // TS: const ctrl = new AbortController()
cts.CancelAfter(TimeSpan.FromMilliseconds(100));        // TS: setTimeout(() => ctrl.abort(), 100)
await service.GetAllAsync(cts.Token);                    // TS: fetch(url, { signal: ctrl.signal })
// -> throws OperationCanceledException (TaskCanceledException is a subclass of it)
```
Rules:
- The **caller** owns the `CancellationTokenSource` and decides when to cancel. Methods only **receive** a `CancellationToken` and **pass it down** to everything they await.
- Convention: it's the **last parameter**, named `cancellationToken`, often with `= default`. `default` means `CancellationToken.None`, a token that's never cancelled.
- Cancellation is **cooperative**: nothing is killed. Code checks the token (`Task.Delay`, EF Core, `HttpClient` do it for you; manual: `cancellationToken.ThrowIfCancellationRequested()`).
- Catch `OperationCanceledException` (the base type), not just `TaskCanceledException`.
- Cancellation is **not an error** you log as a failure. Somebody stopped waiting, that's all.

In our service, `SimulateDatabaseCallAsync` passes the token to `Task.Delay`. Demo section 5: a 300 ms call cancelled after about 100 ms. A `CreateAsync` with an already-cancelled token gives up **before adding anything**: the project doesn't exist afterwards.

## 6. Shared state: `lock` (demo section 7)

```csharp
private readonly Lock _gate = new();      // .NET 9+: a dedicated lock type (older code: private readonly object _gate = new();)

lock (_gate)                              // only ONE thread at a time may run this block
{
    if (_projects.Any(p => ...same name...)) throw ...;   // check
    _projects.Add(project);                                // act
}
```
- `List<T>` is **not thread-safe**. Two threads adding at once can corrupt it, and `_nextProjectId++` isn't atomic either: two threads can read the same value and produce **duplicate ids**.
- **Check-then-act race:** if "is the name taken?" and "add it" were in *separate* steps, two concurrent `CreateAsync("Race project")` calls could both pass the check, and you'd get duplicates. The check and the add must be **in the same lock**. The demo starts 5 concurrent creates with the same name: exactly 1 `created`, 4 `rejected`.
- **You can't `await` inside a `lock`.** The compiler forbids it, because a lock belongs to a thread and an await may resume on another thread. So the service awaits **first** (the simulated I/O), then takes the lock for the quick in-memory part.
- This is the "not thread-safe" limitation from Topic 3, now fixed. With EF Core (Topic 10), the **database** handles concurrency: transactions, unique indexes, and identity columns for ids.

## 7. Pitfalls (interview favourites)

| Pitfall | What goes wrong | Do instead |
|---|---|---|
| `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` ("sync over async") | blocks the thread (starvation); in UI apps and old ASP.NET (with a "synchronization context") it can **deadlock** | `await` all the way up |
| `async void` methods | can't be awaited; an exception inside **crashes the process** | `async Task` (only event handlers use `async void`) |
| calling an async method without `await` (fire-and-forget) | errors are lost; the work may still be running when the request ends. Compiler warning **CS4014** | `await` it (or use a proper background job system) |
| sequential awaits for independent calls | slower than necessary (demo 2: 900 ms vs 300 ms) | start them all, then `await Task.WhenAll(...)` |
| `Thread.Sleep` in async code | blocks a thread | `await Task.Delay(...)` |
| not passing the `CancellationToken` down | work continues after the client is gone | pass it to every async call |
| `Task.Run` around I/O in ASP.NET | just moves the blocking to another pool thread | use a real async API |

`ConfigureAwait(false)`: you'll see it in library code. It means "don't resume on the original synchronization context". ASP.NET Core has no synchronization context, so application code doesn't need it.

**One warning about `Task.WhenAll` with EF Core (Topic 10):** a single `DbContext` doesn't support **parallel** queries. `WhenAll` over several queries on the *same* context throws. Parallel calls are fine for independent things (two HTTP APIs, or separate contexts).

---

## 8. BUILD: what Claude changed and why

### `IProjectService`: async contract
```csharp
Task<IReadOnlyList<Project>> GetAllAsync(CancellationToken cancellationToken = default);
Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default);
Task<Project> CreateAsync(string name, string? description, CancellationToken cancellationToken = default);
Task<TaskItem> AddTaskAsync(int projectId, string title, CancellationToken cancellationToken = default);
```
- **Why async if the data is an in-memory list?** The interface describes the *real* system. The real implementation (EF Core, Topic 10) does I/O and **must** be async. If the interface stayed synchronous, every caller (controllers, tests) would have to change in Topic 10. Designing it async now means only the implementation changes later. That's the "swap implementations" benefit of interfaces from Topic 3.
- Same exceptions and meaning as before; only the shape changed.

### `ProjectService`
| Change | Why |
|---|---|
| constructor gets `TimeSpan simulatedLatency = default` | it **pretends to be a database**: each call waits that long. `default` = zero, so existing code and tests run instantly. The demo uses 300 ms |
| `private Task SimulateDatabaseCallAsync(...) => Task.Delay(_simulatedLatency, cancellationToken);` | stands in for the network + SQL time. `Task.Delay` honours the token. With an already-cancelled token it throws even for a zero delay. Not `async`: it just returns the task |
| `public async Task<...> XxxAsync(..., CancellationToken cancellationToken = default)` | async methods; the token is passed down to the "database call" |
| input validation **before** the await | don't "call the database" with a request that is invalid anyway. Side effect: `AddTaskAsync(42, "")` now reports the empty title before the missing project |
| `private readonly Lock _gate = new();` + `lock (_gate) { ... }` around every list/counter access | async callers run in parallel on different threads (section 6) |
| uniqueness check and `Add` in **one** lock | prevents the check-then-act race |
| `GetAllAsync` returns `_projects.ToList().AsReadOnly()` | a **snapshot** copy, so the caller can loop over it while another request adds a project. Returning the live list would risk "Collection was modified" errors. Still read-only, and the entities inside are still shared (the Topic 3 leak; Topic 6 DTOs fix it) |
| `private Project? FindById(int id)` without a lock | a helper that **assumes the caller holds the lock**, so `AddTaskAsync` can use it inside its own lock (C# locks are re-entrant, but one clear rule is simpler) |

### `playground/04-async.cs`
| Section | Shows |
|---|---|
| 1 | `Task<T>` is pending right after the call; `await` unwraps it |
| 2 | sequential awaits (about 900 ms) vs `Task.WhenAll` (about 300 ms) |
| 3 | the thread id changes across awaits: continuations run on any pool thread |
| 4 | 50 blocking waits vs 50 awaited waits: thread-pool starvation, measured |
| 5 | cancellation with a timeout; an already-cancelled token changes nothing |
| 6 | an exception is stored in the task (`Faulted`) and thrown at the `await` |
| 7 | concurrent creates: the lock keeps names unique and ids distinct |
| 8 | `.Result` blocks the thread for the whole wait |

---

## 9. DEBUG (locally, in Rider): watch awaits and threads

1. Paste this temporarily into `Program.cs`, right before `app.Run();`. Top-level `Program.cs` can use `await` directly.
   ```csharp
   var asyncService = new ProjectHub.Api.Services.ProjectService(
       ProjectHub.Api.Data.SampleData.CreateProjects(), TimeSpan.FromMilliseconds(200));

   Console.WriteLine($"Before: thread {Environment.CurrentManagedThreadId}");
   var first = await asyncService.GetByIdAsync(1);                 // BREAKPOINT A
   Console.WriteLine($"After:  thread {Environment.CurrentManagedThreadId}");

   var three = await Task.WhenAll(
       asyncService.GetByIdAsync(1), asyncService.GetByIdAsync(2), asyncService.GetByIdAsync(3));
   Console.WriteLine($"Got {three.Length} projects");
   ```
2. Set **breakpoint A** on the `var first = await ...` line. Set **breakpoint B** in `ProjectService.GetByIdAsync` on the line `return FindById(id);`.
3. Debug. At A, use **Step Over**. Rider steps *over the await*: the 200 ms wait happens, and you land on the next line. Before you step, check whether breakpoint B gets hit on the way.
4. Resume. B is hit **three times** for the `WhenAll` (one per call). Each time, look at:
   - **Variables:** `id` (1, 2, 3, in which order?)
   - the **Threads** list / the **Parallel Stacks** tab (you saw that tab in your screenshot last time): which thread is running, and are other threads parked at the same place?
5. **Break it (fire-and-forget):** add this line after the `WhenAll` and debug again:
   ```csharp
   asyncService.CreateAsync("Mobile app", null);   // duplicate name, and NO await
   Console.WriteLine("Continued happily");
   ```
   Look at Rider's warning on that line (CS4014). Run it: does anything tell you the create failed? Then add `await` in front and run again. What changes?
6. Clean up: delete the snippet and the breakpoints.

---

## 10. CHECK: answer these in your own words

1. `Task<T>` vs `Promise<T>`: what's the same, and what's the big difference in how the code after `await` runs?
2. **Why should backend I/O be awaited?** (The checkpoint question: say it in two sentences, using "thread" and "pool".)
3. Does async make one request faster? When doesn't async help at all?
4. What does a `CancellationToken` do, who creates it, and where does ASP.NET get one for a request?
5. Why is `.Result` / `.Wait()` bad in a backend?
6. What's wrong with `async void`? With calling an async method without `await`?
7. Why does `ProjectService` need a `lock` now, and why must the name check and the add be inside the **same** lock?
8. Why can't you `await` inside a `lock`?
9. Why is the interface async even though the data is an in-memory list?
10. Sequential `await`s vs `Task.WhenAll`: when is `WhenAll` better, and when is it not allowed (EF Core preview)?
