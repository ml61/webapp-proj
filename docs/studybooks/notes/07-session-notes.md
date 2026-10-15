# Topic 7: notes for the study book (questions, corrections, requests)

- Build: ProjectStoreOptions (+ [Range(0, 10000)]) bound from "ProjectStore" with BindConfiguration +
  ValidateDataAnnotations + ValidateOnStart; appsettings.json 0 ms, appsettings.Development.json 50 ms;
  ProjectService gets optional ILogger<ProjectService> (NullLogger default), logs create/update/delete/add-task AFTER
  the lock with message templates; Program.cs: factory registration of the singleton (options + logger from the
  container); RequestTimingMiddleware (Stopwatch, OnStarting header X-Response-Time-Ms, try/finally log) registered
  first; Labs/Lifetimes: OperationBase + Singleton/Scoped/TransientOperation + scoped LifetimeReporter +
  LifetimesController (GET /api/labs/lifetimes); .http: two new requests.
- Real runs in docs/studybooks/notes/07-runs.txt: lifetimes request 1/2 ids (singleton ef200b0b everywhere; scoped
  222eb6c4 then 34f8a033; transient all different); X-Response-Time-Ms 51 (Development 50 ms); env var
  ProjectStore__SimulatedLatencyMs=500 -> 601 ms (warm-up included); -1 -> OptionsValidationException at startup
  (exit 134); captive dependency (LifetimeReporter as singleton) -> "Cannot consume scoped service ... from singleton"
  at startup (exit 134). HTTPS warning "Failed to determine the https port for redirect" = http-only profile, harmless.
- Tooling gotcha (again): `pkill -f <pattern>` killed my own shell when the same command line contained the pattern
  (I started bin/Debug/.../ProjectHub.Api.dll in that command). Fix: run experiments in a script with `timeout`.
