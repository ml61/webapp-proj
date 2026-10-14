# Topic 4: notes for the study book (questions, corrections, requests)

- Build changes: IProjectService async (`...Async`, `Task<T>`, CancellationToken last param `= default`);
  ProjectService: simulatedLatency ctor param, SimulateDatabaseCallAsync (Task.Delay honours token), validation before the
  await, `Lock _gate` + lock around list/counters, check+add in one lock, GetAllAsync returns a snapshot copy.
- Side effect: AddTaskAsync validates the title before checking the project -> topic 3 demo section 5 adjusted
  (project 42 now gets a valid title so it still shows NotFoundException).
- Demo run (4-core container): sequential 902 ms vs WhenAll 301 ms; blocking 50x500ms = 5511 ms vs async 501 ms;
  cancel after ~110 ms -> TaskCanceledException; 5 concurrent same-name creates -> 1 created, 4 rejected;
  20 concurrent creates -> 20 distinct ids; thread ids across awaits e.g. 7 -> 7 -> 8 -> 8 -> 8 -> 8 -> 7 -> 8 -> 8.
- **Question:** how does `lock` give "exactly 1 created, 4 rejected"? User's scenario: thread 1 passes the check and
  starts adding, thread 2 also passes because thread 1 is not done (different threads).
  Answer: that is exactly what happens WITHOUT the lock. lock = one key: a second thread reaching `lock (_gate)` WAITS
  there (before the check) until the first leaves the block, so check+add is atomic. Two timelines (without / with lock).
  Separate locks for check and add would reopen the gap. JS never needs this (one thread, sync code is never interrupted).
  Terms: race condition, critical section, atomic. Later: DB unique index (topic 10) works across servers; lock = one process.
  Experiment (docs/studybooks/notes/04-race-experiment.cs, Thread.Sleep(10) widens the gap):
    Without lock: created x5 -> 5 projects named 'Race project'
    With lock:    created, rejected x4 -> 1 project
- **User's own conclusion (correct):** "we get info from db in await, then in lock we just do fast C# things, so threads
  don't wait long; it's like a single LOCK for all threads."
  Confirmed + precisions: (1) slow I/O outside the lock, microsecond work inside -> waiting is microseconds; rule: keep
  critical sections short, never do I/O inside a lock (await inside lock is a compile error); with 300 ms inside the lock
  5 creates would take ~1.5 s serially. In our fake the await only simulates DB time; data is read from the list inside
  the lock; with a real DB (topic 10) data comes via await and the DB handles concurrency, the lock disappears.
  (2) one lock PER ProjectService INSTANCE (_gate is an instance field): threads sharing the same service object share
  the lock; different objects = different lists + different locks. Topic 7: registered as a singleton -> one object,
  one list, one lock for all requests. Coarse-grained lock = simplest correct choice; finer options exist
  (ConcurrentDictionary, reader/writer lock).
- **Question:** "5 concurrent creates with the SAME name: rejected, rejected, rejected, rejected, created" — user read it
  as "all 5 rejected" and expected the FIRST one to be created (also changed the title "just in case").
  Answer: the line has 1 created (the last). 4 runs in the container: always exactly 1 created, position varies
  (last, last, first, last). (1) Task.WhenAll returns results in INPUT order (like Promise.all), not completion order.
  (2) Started first != enters the lock first: the 5 waits end almost together, the thread scheduler decides who takes
  the lock. Lock guarantees exactly ONE winner, not WHICH one; correctness must not depend on the winner (if order
  matters: explicit ordering such as a DB sequence or a queue). If the title was changed to an existing name
  (e.g. "Mobile app"), all 5 rejected is correct.
- **DEBUG (user's results):** step 4: breakpoint B hits 1, 3, 2, 1 -> first `1` = the plain await that was stepped over
  (B IS hit during Step Over of an await: debugger stops inside the called method); then WhenAll 3, 2, 1 = reverse of
  start order (same lesson as demo 7: started first != continues first). Step 5: without await the debugger showed the
  BusinessRuleException being thrown but the code continued "happily" (error silently lost inside the faulted task,
  CS4014); with await the exception surfaced at the await and stopped the program before the console line.
- **CHECK round 1:** right: 5 (.Result blocks), 7 (lock + same lock), 9 (async interface for the future), 10 (WhenAll
  for independent calls; sequential when dependent).
  Half: 1 — said "after await the task needs a lock"; correction: await itself needs no lock; the difference is that the
  continuation runs on ANY pool thread, possibly in parallel, so SHARED data needs a lock (JS: one thread, event loop /
  microtasks). 2 (checkpoint) — core right but not crisp; model answer: thread returns to the pool while awaiting I/O;
  blocking holds idle threads -> thread-pool starvation -> queueing/timeouts; few threads serve many requests.
  3 — "no" right, missing: improves throughput/scalability, not single-request latency; no help for CPU-bound work.
  4 — missing that ASP.NET creates the token (HttpContext.RequestAborted, cancelled when the client disconnects; a
  controller just takes a CancellationToken parameter). 6 — missing: exception in async void crashes the process;
  fire-and-forget loses errors (shown in debug step 5), CS4014.
  Wrong: 8 — said "lock is for superfast operations" (that's the guideline); real reason: a lock belongs to the thread
  that took it; after await the method may continue on another thread that would release a lock it doesn't own ->
  compile error. Also add for 5: thread-pool starvation; deadlock in UI / old ASP.NET; for 10: EF Core can't run
  parallel queries on one DbContext.
