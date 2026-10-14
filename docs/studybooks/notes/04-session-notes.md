# Topic 4: notes for the study book (questions, corrections, requests)

- Build changes: IProjectService async (`...Async`, `Task<T>`, CancellationToken last param `= default`);
  ProjectService: simulatedLatency ctor param, SimulateDatabaseCallAsync (Task.Delay honours token), validation before the
  await, `Lock _gate` + lock around list/counters, check+add in one lock, GetAllAsync returns a snapshot copy.
- Side effect: AddTaskAsync validates the title before checking the project -> topic 3 demo section 5 adjusted
  (project 42 now gets a valid title so it still shows NotFoundException).
- Demo run (4-core container): sequential 902 ms vs WhenAll 301 ms; blocking 50x500ms = 5511 ms vs async 501 ms;
  cancel after ~110 ms -> TaskCanceledException; 5 concurrent same-name creates -> 1 created, 4 rejected;
  20 concurrent creates -> 20 distinct ids; thread ids across awaits e.g. 7 -> 7 -> 8 -> 8 -> 8 -> 8 -> 7 -> 8 -> 8.
