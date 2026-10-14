"""Study book for Topic 4: Async/await.

Usage (from repo root):
  python3 scripts/studybooks/04-async-await.py docs/studybooks/04-async-await.pdf [demo-output.txt] [race-output.txt]
Source files are read from src/ and docs/studybooks/notes/ so the printed code always matches the repo.
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

OUT = sys.argv[1]
DEMO_OUT = sys.argv[2] if len(sys.argv) > 2 else None
RACE_OUT = sys.argv[3] if len(sys.argv) > 3 else None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def wrapped(text, width=92):
    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, width, subsequent_indent="    ") or [""])
    return "\n".join(lines)


S = Story()

# ---------------------------------------------------------------- COVER
S += cover("Study book", "Topic 4: Async/await",
           "ProjectHub learning track: React/TypeScript to C#/.NET backend. Week 1, topic 4 of 20.")
S += NOTE([
    "**What this lesson is about.** `Task<T>` is C#'s `Promise<T>` and `async`/`await` read the same as in TS. The real difference is **threads**: "
    "JS has one thread, .NET has a **thread pool**, so code after an `await` can run on any thread, in parallel with other code. "
    "From that follow the key backend ideas: why I/O must be awaited (thread-pool starvation), `CancellationToken` (AbortController), "
    "shared state and `lock` (race conditions), and the classic pitfalls (`.Result`, `async void`, fire-and-forget).",
    "**What we built.** `IProjectService` became async (`...Async`, `Task<T>`, `CancellationToken` on every method). `ProjectService` pretends to be a database "
    "(simulated latency that honours cancellation) and protects its shared list with a `lock`. An 8-section demo measures everything; "
    "a separate experiment proves what happens without the lock.",
    "**Checkpoint.** Explain why backend I/O should be awaited; pass a `CancellationToken` through one path (done: every service method).",
], "Brief overview")
S += H2("Contents")
S += TABLE([
    ["Part", "What is inside"],
    ["1", "TS to C# mapping (Promise, Promise.all, AbortController, ...)"],
    ["2", "One thread vs a thread pool: what really happens at an await"],
    ["3", "Why backend I/O must be awaited (the checkpoint) and what async is not"],
    ["4", "Writing async methods: return types, state machine, exceptions in tasks"],
    ["5", "CancellationToken"],
    ["6", "Shared state and lock: race conditions, check-then-act, your three questions"],
    ["7", "Pitfalls (interview favourites)"],
    ["8", "Our code explained: IProjectService and ProjectService"],
    ["9", "The demo and the race experiment, with real output"],
    ["10", "Debugging in Rider: stepping over awaits, threads, fire-and-forget"],
    ["11", "Your answers, corrections, interview Q&A"],
    ["12", "Summary, cheat sheet, checklist, what comes next"],
], [20, 150])
S += PageBreak()

# ---------------------------------------------------------------- PART 1
S += H1("Part 1. The mapping you already know")
S += TABLE([
    ["TypeScript / JS", "C#", "Note"],
    ["`Promise<T>`", "`Task<T>`", "a value available later"],
    ["`Promise<void>`", "`Task`", "no result, just done (or failed)"],
    ["`async function f(): Promise<T>`", "`async Task<T> FAsync()`", "name ends with **Async** by convention"],
    ["`await p`", "`await t`", "unwraps the result or re-throws the error"],
    ["`Promise.all([a, b])`", "`Task.WhenAll(a, b)`", "wait for all; results in **input order**"],
    ["`Promise.race([a, b])`", "`Task.WhenAny(a, b)`", "first to finish"],
    ["`Promise.resolve(x)`", "`Task.FromResult(x)`", "already completed"],
    ["`new Promise(r => setTimeout(r, 300))`", "`Task.Delay(300)`", "wait without blocking"],
    ["`AbortController`", "`CancellationTokenSource`", "the side that **cancels**"],
    ["`AbortSignal`", "`CancellationToken`", "the side you **pass around**"],
    ["rejected promise", "faulted task", "exception stored until awaited"],
], [60, 52, 58])

# ---------------------------------------------------------------- PART 2
S += H1("Part 2. One thread vs a thread pool")
S += bullets([
    "**JS / Node:** one thread + event loop. After an `await` your code continues on the same single thread (via the microtask queue); two pieces of your code never run at the same moment.",
    "**.NET:** a **thread pool** (starts with about one thread per CPU core, grows slowly). An ASP.NET request runs on a pool thread. At an `await` on real I/O: "
    "(1) the method **pauses** and its thread **goes back to the pool** to serve others; (2) when the I/O completes, **any free pool thread** continues the method.",
])
S += P("Demo section 3: thread ids across 8 awaits: `7 -> 7 -> 8 -> 8 -> 8 -> 8 -> 7 -> 8 -> 8`.")
S += WARN(["You first answered 'after await runs, the task needs a lock'. Correction: `await` itself needs no lock. Because continuations run on **any** pool thread, "
           "**possibly in parallel**, code that touches **shared mutable data** (our list) needs a lock. That is the consequence, not a rule of await."])

# ---------------------------------------------------------------- PART 3
S += H1("Part 3. Why backend I/O must be awaited (the checkpoint)")
S += P("A server handles many requests with a **limited number of threads**, and most of a request's time is **waiting** (database, other APIs, files).")
S += TABLE([
    ["", "Blocking wait (`Thread.Sleep`, `.Result`, `.Wait()`, sync DB calls)", "`await`"],
    ["During the wait", "the thread sits idle and cannot serve anyone", "the thread goes back to the pool and serves other requests"],
    ["Under load", "all threads stuck -> **thread-pool starvation** -> requests queue -> latency, timeouts", "a few threads serve thousands of mostly-waiting requests"],
], [28, 76, 66])
S += CODE("""
50 requests, each waiting 500 ms, 4-core machine (demo section 4):
Blocking  (Thread.Sleep):        5511 ms   <- each request HOLDS a thread; the pool grows slowly
Async     (await Task.Delay):     501 ms   <- no thread held while waiting
""")
S += OK(["**Model answer:** 'While a request awaits I/O, its thread goes back to the pool and serves other requests. Blocking would keep the thread idle; "
         "with many concurrent requests the pool runs out (**thread-pool starvation**), so requests queue and time out. Awaiting lets a few threads serve many requests.'",
         "Order of cause and effect: starvation (all threads stuck) comes **first**; queueing and timeouts follow."], "Checkpoint answer")
S += H2("What async is NOT")
S += bullets([
    "It does **not** make one request faster: a 300 ms query still takes 300 ms. It improves **throughput / scalability**.",
    "It does **not** help **CPU-bound** work (heavy calculations): there is no waiting to give back.",
    "**Async all the way:** once a method is async, callers await it up to the controller. A `.Result` anywhere brings blocking back.",
])

# ---------------------------------------------------------------- PART 4
S += H1("Part 4. Writing async methods")
S += CODE("""
public async Task<Project?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
{
    await SimulateDatabaseCallAsync(cancellationToken); // pause here, thread returns to the pool
    lock (_gate)
    {
        return FindById(id);   // return a Project?; the compiler wraps it in Task<Project?>
    }
}
""")
S += bullets([
    "`async` allows `await` inside and makes the compiler **wrap the return value** in a Task (write `return project;`, not `Task.FromResult`).",
    "Under the hood: a compiler-generated **state machine** that pauses and resumes (like TS generators).",
    "Return types: `Task<T>`, `Task`, `ValueTask<T>` (hot-path optimization; recognize it), `async void` (**only** event handlers).",
    "A method **without** `async` can still return a Task: `LoggingProjectService.GetAllAsync` just returns `inner.GetAllAsync(...)` (pass-through).",
])
S += H2("Exceptions travel inside the task")
S += P("An exception inside an async method is stored in the Task (status `Faulted`) and **re-thrown at the `await`**: `try { await x; } catch` works like JS. "
       "A task that is never awaited loses its exception silently: the C# version of an unhandled promise rejection. Demo section 6: "
       "`Status = WaitingForActivation` right after the call, then the exception at the await, status `Faulted`.")

# ---------------------------------------------------------------- PART 5
S += H1("Part 5. CancellationToken")
S += P("**Why a backend needs it:** the user closes the tab or the client times out, but the server keeps running a long query for nobody. ASP.NET creates a token per request "
       "that is **cancelled when the client disconnects** (`HttpContext.RequestAborted`; in a controller just add a `CancellationToken` parameter, topic 6). "
       "Passed down to EF Core, the database query stops too.")
S += CODE("""
using var cts = new CancellationTokenSource();       // TS: const ctrl = new AbortController()
cts.CancelAfter(TimeSpan.FromMilliseconds(100));     // TS: setTimeout(() => ctrl.abort(), 100)
await service.GetAllAsync(cts.Token);                 // TS: fetch(url, { signal: ctrl.signal })
// -> OperationCanceledException (TaskCanceledException is a subclass)
""")
S += bullets([
    "The **caller** owns the `CancellationTokenSource` and decides when to cancel; methods **receive** the token and **pass it down** to everything they await.",
    "Convention: last parameter, named `cancellationToken`, often `= default` (= `CancellationToken.None`, never cancelled).",
    "**Cooperative**: nothing is killed; code checks the token (`Task.Delay`, EF Core, `HttpClient` do it; manual: `ThrowIfCancellationRequested()`).",
    "Catch `OperationCanceledException` (the base). Cancellation is not a failure to log as an error.",
    "Demo section 5: a 300 ms call cancelled after ~110 ms; `CreateAsync` with an already-cancelled token adds nothing.",
])

# ---------------------------------------------------------------- PART 6
S += PageBreak()
S += H1("Part 6. Shared state and lock")
S += CODE("""
private readonly Lock _gate = new();   // .NET 9+ lock type (older code: private readonly object _gate = new();)

lock (_gate)                           // only ONE thread at a time may run this block
{
    if (_projects.Any(p => ...same name...)) throw ...;   // check
    _projects.Add(project);                                // act
}
""")
S += bullets([
    "`List<T>` is **not thread-safe**, and `_nextProjectId++` is not atomic (two threads can read the same value -> duplicate ids).",
    "**Check-then-act race:** if 'is the name taken?' and 'add it' are separate steps, two concurrent creates can both pass the check.",
    "**No `await` inside a `lock`** (compile error): see 6.3.",
    "With EF Core (topic 10) the **database** handles concurrency (transactions, unique index, identity ids); a `lock` only protects inside one process.",
])
S += H2("6.1 Your question: how does the lock give 'exactly 1 created, 4 rejected'?")
S += P("Your scenario: 'thread 1 passes the check and starts adding; thread 2 also passes because thread 1 is not done'. That is exactly what happens **without** the lock. "
       "`lock` is a door with one key: a second thread reaching `lock (_gate)` **waits there, before the check**, until the first thread leaves the block.")
S += TABLE([
    ["Time", "Without lock: thread 1", "Without lock: thread 2", "With lock: thread 1", "With lock: thread 2"],
    ["t1", "check: taken? No", "", "enters lock", ""],
    ["t2", "", "check: taken? No", "check: taken? No", "reaches lock -> **waits**"],
    ["t3", "Add -> created", "", "Add -> created", "waiting"],
    ["t4", "", "Add -> **duplicate**", "leaves the block", ""],
    ["t5", "", "", "", "enters lock"],
    ["t6", "", "", "", "check: taken? **Yes** -> rejected"],
], [14, 39, 39, 39, 39])
S += P("The check and the add become one **atomic** unit. Separate locks for check and add would reopen the gap. JS never needs this: one thread, so synchronous code is never interrupted. "
       "Terms: **race condition** (result depends on which thread wins), **critical section** (block only one thread may run), **atomic**.")
S += H3("The experiment: the same logic without and with a lock")
S += CODE(src("docs/studybooks/notes/04-race-experiment.cs"), "docs/studybooks/notes/04-race-experiment.cs (Thread.Sleep(10) widens the gap so the race is easy to see)")
if RACE_OUT and os.path.exists(RACE_OUT):
    S += CODE(wrapped(open(RACE_OUT, encoding="utf-8").read()), "Output when the study book was generated:")
S += WARN(["Look at the 'without lock' line: 5 creates all reported 'created', but the list may hold **fewer** than 5 entries (one run gave 4). "
           "Two threads called `List.Add` at the same moment and one item was **silently lost**. Without a lock, a `List<T>` does not only allow duplicates: it can lose or corrupt data. "
           "Race bugs are rare, random and load-dependent: 'it worked when I tested it' proves nothing."], "Even worse than duplicates")
S += H2("6.2 Your conclusion: slow wait outside, fast work inside, one lock")
S += P("You concluded: 'we get the data in the await, then inside the lock we only do fast C# things, so threads do not wait long; it is like one single lock for all threads'. Correct, with two precisions:")
S += numbered([
    "**Keep critical sections short.** The 300 ms wait is **outside** the lock; inside are microseconds, so waiting threads wait microseconds. With the wait inside, 5 creates would take ~1.5 s one after another. "
    "In our fake the await only *simulates* the database time; the data is read from the list inside the lock. With a real database the data comes through the await and the DB handles concurrency.",
    "**One lock per `ProjectService` object** (`_gate` is an instance field). Threads using the same service object share the lock (they share the list). Different objects = different lists + different locks. "
    "Topic 7 registers the service as a **singleton**: one object, one list, one lock for all requests.",
])
S += P("Design trade-off: one lock for every operation is **coarse-grained**: the simplest correct choice; fine because the work inside is tiny. Finer tools exist (`ConcurrentDictionary`, reader/writer locks).", small)
S += H2("6.3 Your question: 'why were all 5 rejected?'")
S += P("You saw `rejected, rejected, rejected, rejected, created` and expected the **first** call to win. The line actually has **1 created** (the last). Four runs gave: last, last, first, last.")
S += numbered([
    "`Task.WhenAll` returns results in **input order** (like `Promise.all`), not completion order: position 5 = 'the 5th call started'.",
    "**Started first does not mean enters the lock first.** The five 300 ms waits end almost together; the **thread scheduler** decides who takes the lock.",
])
S += OK(["A lock guarantees **exactly one winner**, not **which one**. Correct code must not depend on the winner; if order matters, use explicit ordering (a DB sequence, a queue). "
         "If the title was changed to an **existing** name (e.g. 'Mobile app'), all 5 rejected is correct."])
S += H2("6.4 Why await is forbidden inside a lock")
S += P("A lock **belongs to the thread that took it**. After an `await` the method may continue on **another thread**, which would try to release a lock it does not own. "
       "So the compiler forbids `await` inside `lock`. ('Locks are for short operations' is the design guideline, not the reason for this rule.)")

# ---------------------------------------------------------------- PART 7
S += H1("Part 7. Pitfalls (interview favourites)")
S += TABLE([
    ["Pitfall", "What goes wrong", "Do instead"],
    ["`.Result`, `.Wait()`, `.GetAwaiter().GetResult()` (sync over async)", "blocks the thread (starvation); in UI apps / old ASP.NET it can **deadlock**", "`await` all the way"],
    ["`async void`", "cannot be awaited; an exception inside **crashes the process**", "`async Task` (event handlers only)"],
    ["async call without `await` (fire-and-forget)", "errors silently lost; work may outlive the request; warning **CS4014**", "`await` it (or a real background job system)"],
    ["sequential awaits for independent calls", "slower (demo 2: 902 ms vs 301 ms)", "start all, then `await Task.WhenAll(...)`"],
    ["`Thread.Sleep` in async code", "blocks a thread", "`await Task.Delay(...)`"],
    ["not passing the `CancellationToken` down", "work continues after the client left", "pass it to every async call"],
    ["`Task.Run` around I/O in ASP.NET", "just moves the blocking to another pool thread", "a real async API"],
    ["`Task.WhenAll` over queries on one EF `DbContext`", "throws: a DbContext does not support parallel queries", "sequential awaits, or separate contexts"],
], [52, 66, 52])
S += P("`ConfigureAwait(false)`: seen in library code ('do not resume on the original synchronization context'). ASP.NET Core has no synchronization context, so application code does not need it.", small)

# ---------------------------------------------------------------- PART 8
S += PageBreak()
S += H1("Part 8. Our code, explained")
S += H2("8.1 The async contract")
S += CODE(src("src/ProjectHub.Api/Services/IProjectService.cs"), "src/ProjectHub.Api/Services/IProjectService.cs")
S += P("**Why async when the data is an in-memory list?** The interface describes the *real* system. EF Core (topic 10) does I/O and must be async; "
       "if the interface stayed synchronous, every caller (controllers, tests) would change in topic 10. Now only the implementation changes: the 'swap implementations' benefit from topic 3.")
S += H2("8.2 The implementation")
S += CODE(src("src/ProjectHub.Api/Services/ProjectService.cs"), "src/ProjectHub.Api/Services/ProjectService.cs")
S += TABLE([
    ["Change", "Why"],
    ["constructor parameter `TimeSpan simulatedLatency = default`", "pretends to be a database; `default` = zero so tests run instantly; the demo uses 300 ms"],
    ["`SimulateDatabaseCallAsync` => `Task.Delay(_simulatedLatency, cancellationToken)`", "stands in for network + SQL time; honours the token (an already-cancelled token throws even for zero delay); not `async`, it just returns the task"],
    ["`public async Task<...> XxxAsync(..., CancellationToken cancellationToken = default)`", "async methods; the token is passed down"],
    ["validation **before** the await", "do not 'call the database' with an invalid request. Side effect: `AddTaskAsync(42, \"\")` now reports the empty title first (the topic 3 demo was adjusted)"],
    ["`private readonly Lock _gate = new();` + `lock (_gate)` around list and counters", "continuations run in parallel on different threads"],
    ["name check and `Add` in **one** lock", "prevents the check-then-act race"],
    ["`GetAllAsync` returns `_projects.ToList().AsReadOnly()`", "a **snapshot**: callers can loop while others add (no 'Collection was modified'); still read-only; entities still shared (topic 3 leak, fixed by DTOs in topic 6)"],
    ["`private Project? FindById(int id)` without a lock", "helper that assumes the caller holds the lock"],
], [76, 94])

# ---------------------------------------------------------------- PART 9
S += H1("Part 9. The demo: playground/04-async.cs")
S += P("Run from the repo root: `dotnet run playground/04-async.cs` (listed in Rider's `playground` solution folder). Timings depend on the machine.")
S += TABLE([
    ["#", "Shows"],
    ["1", "`Task<T>` pending right after the call; `await` unwraps it"],
    ["2", "sequential awaits (~900 ms) vs `Task.WhenAll` (~300 ms)"],
    ["3", "thread id changes across awaits"],
    ["4", "50 blocking vs 50 awaited waits: thread-pool starvation, measured"],
    ["5", "cancellation with a timeout; an already-cancelled token changes nothing"],
    ["6", "exception stored in the task (Faulted), thrown at the await"],
    ["7", "concurrent creates: the lock keeps names unique and ids distinct"],
    ["8", "`.Result` blocks the thread for the whole wait"],
], [10, 160])
if DEMO_OUT and os.path.exists(DEMO_OUT):
    S += CODE(wrapped(open(DEMO_OUT, encoding="utf-8").read()), "Full output (captured in the cloud container, 4 cores):")

# ---------------------------------------------------------------- PART 10
S += PageBreak()
S += H1("Part 10. Debugging: awaits and threads in Rider")
S += CODE("""
var asyncService = new ProjectHub.Api.Services.ProjectService(
    ProjectHub.Api.Data.SampleData.CreateProjects(), TimeSpan.FromMilliseconds(200));

Console.WriteLine($"Before: thread {Environment.CurrentManagedThreadId}");
var first = await asyncService.GetByIdAsync(1);                 // BREAKPOINT A
Console.WriteLine($"After:  thread {Environment.CurrentManagedThreadId}");

var three = await Task.WhenAll(
    asyncService.GetByIdAsync(1), asyncService.GetByIdAsync(2), asyncService.GetByIdAsync(3));
Console.WriteLine($"Got {three.Length} projects");
""", "Temporary snippet in Program.cs before app.Run() (top-level Program.cs can await directly):")
S += numbered([
    "Breakpoint **A** on `var first = await ...`; breakpoint **B** in `ProjectService.GetByIdAsync` on `return FindById(id);`.",
    "Debug; at A use **Step Over**: Rider steps over the await (the wait happens, you land on the next line).",
    "Resume: B is hit for each `WhenAll` call; look at `id`, the Threads list and the **Parallel Stacks** tab.",
    "Break it: add `asyncService.CreateAsync(\"Mobile app\", null);` (no await) + `Console.WriteLine(\"Continued happily\");`; then add `await`.",
    "Clean up the snippet and breakpoints.",
])
S += H2("What you observed")
S += TABLE([
    ["Step", "Result", "Meaning"],
    ["Step Over at A", "B was hit with `id = 1`", "breakpoints inside the awaited method **are** hit while stepping over an await"],
    ["WhenAll", "B hit with `id` 3, 2, 1", "reverse of the start order: started first != continues first (same as demo 7)"],
    ["Without `await`", "the debugger showed the `BusinessRuleException` being thrown, but 'Continued happily' was printed", "the error was **silently lost** inside a faulted task nobody awaited (fire-and-forget, CS4014)"],
    ["With `await`", "no 'Continued happily'", "the exception surfaced at the await and stopped the program"],
], [30, 66, 74])

# ---------------------------------------------------------------- PART 11
S += PageBreak()
S += H1("Part 11. Your answers, corrections, interview Q&A")
S += H2("11.1 CHECK round 1")
S += TABLE([
    ["Question", "Your answer", "Complete answer"],
    ["1. Task vs Promise", "same: a result later; JS continues via event loop/microtasks (good); 'after await the task needs a lock' (**wrong**)", "continuation on any pool thread, possibly in parallel -> shared data needs a lock; await itself needs none"],
    ["2. Why await I/O (checkpoint)", "thread goes back to the pool while the DB works (core right, not crisp)", "see the model answer in Part 3 (starvation, queueing, few threads serve many)"],
    ["3. Faster?", "'no' (right); 'when we don't need await, async makes no sense'", "improves throughput/scalability, not single-request speed; no help for CPU-bound work"],
    ["4. CancellationToken", "cancels the operation, EF stops; the requester creates it (right)", "plus: methods pass it down; ASP.NET creates it per request (cancelled on client disconnect)"],
    ["5. .Result / .Wait()", "blocks the thread until the end (right)", "plus: thread-pool starvation; deadlock in UI / old ASP.NET"],
    ["6. async void / no await", "'cannot be awaited' (half)", "exception in async void crashes the process; fire-and-forget loses errors (you saw it in debug)"],
    ["7. lock + same lock", "right", ""],
    ["8. No await in lock", "'lock is for superfast operations' (**wrong reason**)", "lock belongs to a thread; after await another thread may continue -> compile error"],
    ["9. Async interface", "for the future real DB/HTTP (right)", ""],
    ["10. WhenAll vs sequential", "WhenAll for independent calls; sequential when dependent (right)", "plus: no parallel queries on one EF DbContext"],
], [32, 66, 72])
S += H2("11.2 Re-check")
S += TABLE([
    ["Question", "Your answer", "Verdict"],
    ["A. Checkpoint", "thread goes back to the pool during async work; otherwise it sits idle, requests queue, starvation", "right; order: starvation first, then queueing"],
    ["B. await in lock", "lock belongs to the thread that took it; after await another thread may continue, release impossible", "right (it is a compile error)"],
    ["C. What async improves / not", "threads are constantly used, not idle", "half: say **throughput/scalability**, and **no help for CPU-bound work**"],
], [36, 76, 58])
S += H2("11.3 Interview questions with model answers")
qa = [
    ("Task vs Promise?", "Both represent a future result; await unwraps or re-throws. In .NET the continuation runs on any thread-pool thread, possibly in parallel; JS has one thread."),
    ("Why should backend I/O be awaited?", "The thread returns to the pool while waiting and serves other requests; blocking keeps threads idle and leads to thread-pool starvation, queueing and timeouts."),
    ("Does async make a request faster?", "No. It improves throughput/scalability. It does not help CPU-bound work."),
    ("What is thread-pool starvation?", "All pool threads are blocked waiting, so new work queues up; the pool grows slowly; latency and timeouts follow."),
    ("What is a CancellationToken? Who creates it?", "A signal that work is no longer needed (AbortSignal). The caller owns the CancellationTokenSource; methods receive the token and pass it down. ASP.NET supplies one per request, cancelled when the client disconnects."),
    ("Why is .Result / .Wait() bad?", "Sync over async: blocks a thread (starvation) and can deadlock where a synchronization context exists (UI, old ASP.NET)."),
    ("What is wrong with async void?", "It cannot be awaited and an exception inside it crashes the process. Use async Task; async void only for event handlers."),
    ("What happens if you call an async method without await?", "Fire-and-forget: the exception is stored in a task nobody observes and is lost; the work may outlive the request (CS4014)."),
    ("Where does an exception in an async method surface?", "It is stored in the task (Faulted) and re-thrown at the await."),
    ("Task.WhenAll vs sequential awaits?", "WhenAll for independent operations (they overlap); sequential when each depends on the previous. Not for parallel queries on one EF DbContext."),
    ("What order does Task.WhenAll return results in?", "The order of the input tasks, not completion order (like Promise.all)."),
    ("What is a race condition? Check-then-act?", "The result depends on thread timing. Check-then-act: two threads both pass a check before either acts; fix by making check+act atomic (one lock, or a DB constraint)."),
    ("Why can't you await inside a lock?", "A lock belongs to the thread that took it; after await another thread may continue and could not release it. Compile error."),
    ("Is List<T> thread-safe?", "No: concurrent Add can lose items or corrupt the list; protect it with a lock or use a concurrent collection."),
    ("What does a lock guarantee about the winner?", "Exactly one thread at a time in the critical section; not which thread goes first."),
    ("Why keep critical sections short?", "Every other thread waits while one holds the lock; never do I/O inside it."),
    ("Why make the interface async if the implementation is in-memory?", "The interface describes the real system (EF Core I/O). Making it async now means callers will not change when the implementation does."),
    ("What does ConfigureAwait(false) do? Needed in ASP.NET Core?", "Do not resume on the captured synchronization context. ASP.NET Core has none, so application code does not need it."),
]
for q, a in qa:
    S += QA(q, a)

# ---------------------------------------------------------------- PART 12
S += PageBreak()
S += H1("Part 12. Summary")
S += OK([
    "`Task<T>` = `Promise<T>`; `Task.WhenAll` = `Promise.all` (input order); `CancellationToken` = `AbortSignal`.",
    "**Thread pool**: at an await on I/O the thread returns to the pool; any free thread continues the method, possibly in parallel with other code.",
    "**Why await I/O**: threads serve other requests while waiting; blocking -> **thread-pool starvation** -> queueing, timeouts. Async improves **throughput**, not single-request speed; no help for CPU-bound work.",
    "Async methods: `async Task<T> XxxAsync(..., CancellationToken cancellationToken = default)`; exceptions surface at the await; async all the way.",
    "**Cancellation**: caller owns the source; methods pass the token down; ASP.NET cancels it when the client disconnects; cooperative; not an error.",
    "**Shared state**: `List<T>` is not thread-safe; check + act in **one** `lock`; keep critical sections short; no await inside a lock; one lock per service object; a lock guarantees one winner, not which.",
    "**Pitfalls**: `.Result`/`.Wait()`, `async void`, fire-and-forget, sequential independent awaits, `Thread.Sleep`, parallel queries on one DbContext.",
], "Key takeaways")
S += H2("Cheat sheet")
S += TABLE([
    ["TS / JS", "C#"],
    ["`async function getById(id): Promise<Project | null>`", "`async Task<Project?> GetByIdAsync(int id, CancellationToken ct = default)`"],
    ["`await Promise.all([a(), b()])`", "`await Task.WhenAll(A(), B())`"],
    ["`await new Promise(r => setTimeout(r, 300))`", "`await Task.Delay(300, ct)`"],
    ["`const c = new AbortController(); c.abort()`", "`using var cts = new CancellationTokenSource(); cts.Cancel()`"],
    ["`fetch(url, { signal })`", "`await http.GetAsync(url, ct)`"],
    ["`try { await p } catch (e) { }`", "`try { await t; } catch (SomeException ex) { }`"],
    ["(no equivalent: one thread)", "`lock (_gate) { /* check + act */ }`"],
], [80, 90])
S += H2("Checklist: can you do this without notes?")
S += bullets([
    "Give the checkpoint answer in two sentences with 'thread', 'pool', 'starvation'.",
    "Explain what happens to the thread at an await, and why code after it may run on another thread.",
    "Explain what async improves and where it does not help.",
    "Explain CancellationToken: who creates it, who passes it, where ASP.NET gets it.",
    "Name the pitfalls: .Result, async void, fire-and-forget, Thread.Sleep, WhenAll on one DbContext.",
    "Draw the two timelines (with / without lock) for check-then-act.",
    "Explain why await is not allowed inside a lock.",
    "Explain why IProjectService is async although the data is in memory.",
])
S += H2("What comes next: Topic 5 (Debugging fundamentals, Debug Lab A)")
S += P("A focused local lab in Rider: find a real bug without `Console.WriteLine`, using breakpoints, Step Into/Over/Out, Watches, conditional breakpoints, "
       "the call stack and exception settings. You have already used most of these tools; topic 5 puts them together on a planted bug in ProjectHub.")

build(OUT, S, "ProjectHub study book | Topic 4: Async/await", "ProjectHub study book: Topic 4, Async/await")
print("ok", OUT)
