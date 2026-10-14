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
