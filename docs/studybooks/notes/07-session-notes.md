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
- **Question:** "what is composition — like anti-inheritance? so like independent?" -> Not quite: another way to reuse
  code. Inheritance = IS-A (`class X : BaseClass`, become a subtype); composition = HAS-A (hold other objects as
  fields/ctor params and call them). React analogy: React docs "Composition vs Inheritance" — components built OUT OF
  components (children, props, hooks), never `extends Button`. Our code: `ProjectsController(IProjectService projects)
  : ControllerBase` has both (has-a service, is-a ControllerBase); ProjectService has List/Lock/ILogger;
  LoggingProjectService wraps an inner IProjectService (decorator = composition); DashboardReport has IProjectService.
  Why prefer: swappable parts (DI, EF in topic 10, fakes in tests), only one base class, no fragile base class,
  small focused classes instead of deep hierarchies. "Independent" is partly right: LOOSELY COUPLED (doesn't know
  which implementation) but still DEPENDS on the part's interface — DI plugs it in. Inheritance stays normal for
  framework base classes and real is-a families. One-sentence interview answer recorded in chat.
- **Question:** "Is `app.MapControllers()` responsible for all controllers being seen? LifetimesController works but is
  not in the Controllers folder; the app understands itself what can be queried?" -> YES, two steps, folder irrelevant:
  (1) `AddControllers()` DISCOVERS controllers by reflection over the compiled assembly: public, non-abstract, and
  (inherits ControllerBase OR name ends with "Controller" OR has [Controller]/[ApiController]); namespace/folder don't
  matter (Controllers/ is a human convention). (2) `MapControllers()` reads [Route] + [HttpGet...] and registers
  ENDPOINTS (URL+verb -> action) that routing matches. Missing MapControllers -> every request 404; missing
  AddControllers -> MapControllers fails at startup asking for AddControllers. Analogies: NestJS decorators
  (@Controller/@Get) = attributes; Next.js is the opposite (folder IS the route). See all discovered endpoints at
  /openapi/v1.json.
- **User ran the lifetimes lab themselves (2 requests in one session):** "singleton same during run/debug session;
  scoped per request; transient always unique, just in a scope of a class or something" -> Q1 answered. Precisions:
  singleton = lifetime of the app PROCESS (restart -> new id; also why in-memory projects reset on restart);
  transient = per INJECTION (every resolution), not per class: a class asking twice gets two objects; controller and
  reporter asked once each -> 2 ids per request. Interview lines: singleton one per app; scoped one per HTTP request;
  transient new every time it's injected.
- **Observation/question:** "in C# we can pass a class as a generic, like app.UseMiddleware<RequestTimingMiddleware>()".
  Answer: possible because C# generics are REIFIED (topic 3): the method uses typeof(T) at runtime -> finds the
  constructor -> asks DI for the parameters (passes `next` itself) -> creates the object -> calls InvokeAsync per
  request; we never `new` it. TS generics are erased, so TS libraries pass the CLASS AS A VALUE (Express: create it
  yourself; NestJS/Inversify: class object as token). C# also has `app.UseMiddleware(typeof(RequestTimingMiddleware))`;
  generic form preferred. Same pattern: AddSingleton<SingletonOperation>(), AddOptions<ProjectStoreOptions>(),
  GetRequiredService<ILogger<ProjectService>>(), ILogger<T> (category), IOptions<T>. Bonus: constraints check at
  compile time: AddSingleton<TService, TImplementation>() where TImplementation : class, TService ->
  AddSingleton<IProjectService, SampleData>() doesn't compile.
- **User's summary (correct):** "to make DI work we register it (ProjectService factory, AddSingleton/AddScoped/
  AddTransient...), then use it in a constructor — not just in controllers, in any class". Precision: only in classes
  THE CONTAINER CREATES. Chain: ASP.NET creates LifetimesController -> needs LifetimeReporter (registered) -> needs the
  3 operations (registered). If YOU `new` a class, no DI (playground demos `new ProjectService(...)`). Rule: in app code
  don't `new` services, ask for them. Two registration styles: by type (`AddScoped<LifetimeReporter>()`, container
  calls the ctor, all params must be registered) vs factory (`sp => new ProjectService(...)`, ctor needs non-services
  like List/TimeSpan). Everyday form: interface -> class `AddScoped<IProjectService, ProjectService>()` (topic 10).
  Forgotten registration -> "Unable to resolve service for type 'X' while attempting to activate 'Y'" (checked at
  startup in Development). Interview one-liner recorded in chat.
- **Question:** `controller = new { singleton = singleton.Id, scoped = scoped.Id, transient = transient.Id }` — "just
  creates an object which we return in the HTTP response?" -> YES: an ANONYMOUS TYPE (topic 2), like a JS object
  literal; nested inside the outer `new { controller = ..., reporter = ... }`; Ok(...) -> System.Text.Json ->
  {"controller":{"singleton":"ef200b0b",...},"reporter":{...}}. Compiler-generated class, read-only properties, no
  writable name (can't be ActionResult<T>), still strongly typed. Lab uses it for brevity (IActionResult); real
  endpoints use record DTOs: named contract, OpenAPI can describe it -> typed frontend client, reusable, testable.
- **DEBUG step 1 (user):** breakpoint in OperationBase: "3*2 stops for 1st and 2nd request; Rider's debugger (bug)
  icon shows a counter 2 -> like 2 sessions; that's the problem, otherwise the 2nd request wouldn't have the
  singleton". Correct diagnosis: TWO debug sessions = two API processes; each process has its own singleton
  ("one per app" = one per running PROCESS); request 2 hitting the other process creates its singleton again.
  How both answer one port: `localhost` = IPv4 127.0.0.1 + IPv6 ::1; second instance can bind the other address
  (Kestrel only warns when it can't bind both). Fix: stop ALL sessions (red stop in each Debug tab, counter gone),
  start one. Expected with one process: request 1 -> 4 stops (SingletonOperation lazily on first need, ScopedOperation
  once, TransientOperation twice); request 2 -> 3 stops (no singleton). Lesson: when observation contradicts the
  model, check the environment first (topic 5 stale build, now two processes).
