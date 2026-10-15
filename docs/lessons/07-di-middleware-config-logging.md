# Lesson 7: Dependency injection, middleware, configuration, ILogger

**Roadmap:** Week 2, Topic 7. **Time:** about 2–3 h.
**Checkpoint:** you can explain **Scoped vs Transient vs Singleton**, and the API has a request-timing middleware.

**Files for this lesson:**
- `src/ProjectHub.Api/Program.cs`: registrations (DI), options, middleware order
- `src/ProjectHub.Api/Middleware/RequestTimingMiddleware.cs`: our first middleware
- `src/ProjectHub.Api/Configuration/ProjectStoreOptions.cs` + `appsettings.json` / `appsettings.Development.json`: settings
- `src/ProjectHub.Api/Services/ProjectService.cs`: now writes logs with `ILogger`
- `src/ProjectHub.Api/Labs/Lifetimes/*`: **lifetimes lab**, `GET /api/labs/lifetimes`
- `src/ProjectHub.Api/ProjectHub.Api.http`: two new requests at the bottom

---

## 1. Dependency injection: what and why

**Without DI**, a class creates what it needs:
```csharp
public class ProjectsController
{
    private readonly ProjectService _projects = new ProjectService(SampleData.CreateProjects(), ...); // hard-wired
}
```
- The controller decides the **concrete class**, its **constructor arguments**, and its **lifetime**. All of that is hidden inside it.
- You can't swap it (EF Core in Topic 10), you can't fake it in a test (Topic 13), and every controller would create its **own** store.

**With DI**, a class only **declares** what it needs, and something else provides it:
```csharp
public class ProjectsController(IProjectService projects) : ControllerBase   // "I need an IProjectService"
```
```csharp
builder.Services.AddSingleton<IProjectService>(...);                         // Program.cs: "here's how to make one"
```
- **The DI container** (`builder.Services`) is a registry: *type → how to create it → how long it lives*.
- **Registration** happens once, in `Program.cs` (the **composition root**, the one place where the app is wired together).
- **Resolution:** when ASP.NET creates a controller for a request, it looks at the constructor parameters, creates or reuses each dependency (and *their* dependencies, recursively), and passes them in. This is **constructor injection**.
- It's called **inversion of control**: the class no longer controls how its dependencies are created.

**TS / React analogy:** in Node you'd usually `import` a module-level singleton (hard-wired), or pass dependencies by hand. **Angular** has DI just like this. In React, **Context** is the closest thing: a provider at the top, `useContext` deep inside. The component doesn't create the value, it receives it.

Topic 3 built it by hand: `ProjectService` *received* its data in the constructor. The container now automates that, at every level.

## 2. The three lifetimes (the checkpoint)

| Lifetime | Registration | One object per… | Typical use |
|---|---|---|---|
| **Singleton** | `AddSingleton<T>()` | **application** (created once, shared by all requests and threads) | caches, configuration, our in-memory store. **Must be thread-safe** |
| **Scoped** | `AddScoped<T>()` | **HTTP request** (the request is the "scope") | EF Core's `DbContext` (Topic 10), anything holding per-request state (current user, unit of work) |
| **Transient** | `AddTransient<T>()` | **every injection** (a new object each time anyone asks) | small, stateless, cheap helpers |

### Proof: the lifetimes lab (real output)
`GET /api/labs/lifetimes` injects one of each into the controller **and** into a second consumer (`LifetimeReporter`) in the same request. Each object gets a random id when it's **created**:
```
request 1  controller: singleton ef200b0b  scoped 222eb6c4  transient 08a150dd
           reporter:   singleton ef200b0b  scoped 222eb6c4  transient ace29ac3
request 2  controller: singleton ef200b0b  scoped 34f8a033  transient 69a01101
           reporter:   singleton ef200b0b  scoped 34f8a033  transient 9d9ee21f
```
| Lifetime | Same within one request? | Same across requests? | Read from the output |
|---|---|---|---|
| Singleton | yes | **yes** | `ef200b0b` everywhere |
| Scoped | **yes** | no | `222eb6c4` twice in request 1, `34f8a033` in request 2 |
| Transient | **no** | no | 4 different ids |

### How to choose
- **Default for app services: Scoped**, when they work with a `DbContext` (Topic 10). A service can't live longer than what it holds.
- **Singleton** only for things that are truly shared **and thread-safe**. Our `ProjectService` is a singleton because it *is* the in-memory store, and Topic 4's `lock` makes it safe. In Topic 10 it becomes **Scoped**, because it will use a `DbContext`.
- **Transient** for lightweight stateless helpers.

### The rule you must not break: no "captive dependencies"
**A service may not depend on a service with a shorter lifetime.** A singleton that receives a scoped object keeps it **forever**: the "per-request" object gets captured and reused by every later request (imagine one request's `DbContext` shared by all users). ASP.NET checks this in Development and **refuses to start**:
```
Cannot consume scoped service 'ProjectHub.Api.Labs.Lifetimes.ScopedOperation'
from singleton 'ProjectHub.Api.Labs.Lifetimes.LifetimeReporter'.
```
(We triggered it on purpose by registering `LifetimeReporter` as a singleton; it's the DEBUG step "break it" in section 9.)

| A … may depend on a … | Singleton | Scoped | Transient |
|---|---|---|---|
| **Singleton** | ✅ | ❌ captive | ⚠️ allowed, but it lives as long as the singleton |
| **Scoped** | ✅ | ✅ | ✅ |
| **Transient** | ✅ | ✅ | ✅ |

Also: the container **disposes** (`IDisposable.Dispose()`) scoped and transient objects when the request ends, and singletons when the app stops.

## 3. Middleware: the request pipeline

Every request passes through a **chain of middleware** before it reaches a controller, and the response passes back out through the same chain in reverse. It works like an onion:
```
request  → RequestTiming → HttpsRedirection → Authorization → [routing → controller action]
response ← RequestTiming ← HttpsRedirection ← Authorization ←
```
Each middleware can do work **before** calling `next`, call `next` (the rest of the pipeline), do work **after**, or **short-circuit**: not call `next`, and answer right away (an auth middleware returning 401, for example).

**Express mapping:**
```js
app.use(async (req, res, next) => { const start = Date.now(); await next(); log(Date.now() - start); });
```
```csharp
public class RequestTimingMiddleware(RequestDelegate next, ILogger<RequestTimingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();
        context.Response.OnStarting(() => { context.Response.Headers["X-Response-Time-Ms"] = ...; return Task.CompletedTask; });
        try { await next(context); }                       // the rest of the pipeline runs here
        finally { logger.LogInformation("HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs} ms", ...); }
    }
}
```
- **`RequestDelegate next`**: "the rest of the pipeline", the same as Express's `next`. **`HttpContext`**: the request and response, the same as `req` + `res`.
- **`Response.OnStarting(...)`**: headers can only be changed **before** the response starts being sent (status line and headers go first). By the time `await next` returns, the controller may already have written the body. `OnStarting` registers a callback that runs right at the last moment headers can still be changed.
- **`try/finally`**: log even if something further down throws. (The status code logged for an unhandled exception may still say 200, because the 500 is produced later. Topic 12's handler fixes that.)
- **Registered with `app.UseMiddleware<RequestTimingMiddleware>()`, first in the pipeline**, so its stopwatch includes everything after it. **Order matters**: a middleware only sees what happens *after* it in the chain.
- **A middleware class is created once** (it behaves like a singleton). Scoped services must therefore be taken as **parameters of `InvokeAsync`**, not in the constructor, or you get the captive-dependency problem again.

The ones already in our `Program.cs`: `UseHttpsRedirection` (redirect http → https), `UseAuthorization` (Topic 16), and `MapControllers` (the endpoint at the end of the chain).

About the startup warning `Failed to determine the https port for redirect`: we run the **http-only** profile, so HTTPS redirection has nowhere to redirect to and does nothing. It's harmless here.

## 4. Configuration

### Where settings come from (later sources override earlier ones)
1. `appsettings.json`: defaults for all environments
2. `appsettings.{Environment}.json`: e.g. `appsettings.Development.json`. The environment comes from `ASPNETCORE_ENVIRONMENT`, which `launchSettings.json` sets to `Development` locally.
3. **User secrets** (Development only, stored outside the repo)
4. **Environment variables**: nested keys use **double underscore**: `ProjectStore__SimulatedLatencyMs=500`
5. Command-line arguments

That's how one build runs everywhere: Development gets 50 ms latency from `appsettings.Development.json`, production uses the 0 from `appsettings.json`, and a server or Azure (Topic 19) can override anything with environment variables, without changing files. **Secrets** (passwords, keys) never go in `appsettings.json` in git: user secrets locally, Key Vault in Azure (Topic 19).

### The Options pattern: settings as a typed class
```json
"ProjectStore": { "SimulatedLatencyMs": 50 }
```
```csharp
public class ProjectStoreOptions
{
    public const string SectionName = "ProjectStore";
    [Range(0, 10_000)] public int SimulatedLatencyMs { get; set; }
}

builder.Services.AddOptions<ProjectStoreOptions>()
    .BindConfiguration(ProjectStoreOptions.SectionName)   // JSON section → object
    .ValidateDataAnnotations()                            // check [Range]
    .ValidateOnStart();                                   // fail at STARTUP, not on some random request later
```
- Then anyone can inject **`IOptions<ProjectStoreOptions>`** and read `.Value.SimulatedLatencyMs`. It's typed, with no `"ProjectStore:SimulatedLatencyMs"` strings scattered around.
- Variants: `IOptions<T>` (read once, singleton-friendly), `IOptionsSnapshot<T>` (re-read per request, scoped), `IOptionsMonitor<T>` (live updates when the file changes).
- **Fail fast:** with `-1` the app **refuses to start**:
  `OptionsValidationException: ... 'SimulatedLatencyMs' with the error: 'The field SimulatedLatencyMs must be between 0 and 10000.'` That's better than discovering a bad setting at 3 a.m. on the first request that uses it.

### Real experiments (cloud container)
| Experiment | Result |
|---|---|
| Development profile (`appsettings.Development.json`: 50) | `X-Response-Time-Ms: 51` on `GET /api/projects` |
| `ProjectStore__SimulatedLatencyMs=500` environment variable | `X-Response-Time-Ms: 601` (500 ms + first-request warm-up): the env var **overrode** the JSON |
| `ProjectStore__SimulatedLatencyMs=-1` | app aborted at startup with the `OptionsValidationException` above |

## 5. ILogger: structured logging

```csharp
public ProjectService(..., ILogger<ProjectService>? logger = null)
...
_logger.LogInformation("Created project {ProjectId} {ProjectName}", project.Id, project.Name);
```
Output:
```
info: ProjectHub.Api.Services.ProjectService[0]
      Created project 4 Docs portal
info: ProjectHub.Api.Middleware.RequestTimingMiddleware[0]
      HTTP POST /api/projects responded 201 in 123 ms
```
- **`ILogger<T>`**: injected by DI. `T` becomes the **category** (`ProjectHub.Api.Services.ProjectService`), so you can see where a line came from, and set levels per category.
- **Levels** (lowest → highest): `Trace`, `Debug`, `Information`, `Warning`, `Error`, `Critical`. `appsettings.json` → `Logging:LogLevel` sets the minimum per category: `"Default": "Information"`, `"Microsoft.AspNetCore": "Warning"`. That's why the framework itself is quiet and our lines show.
- **Message templates, not string interpolation (an interview favourite):**
  ```csharp
  _logger.LogInformation("Created project {ProjectId}", project.Id);   // ✅ structured: ProjectId is a separate FIELD
  _logger.LogInformation($"Created project {project.Id}");             // ❌ just text, the value is baked in
  ```
  With a template, log systems (Application Insights, Seq, Elastic: Topics 17 and 19) store `ProjectId = 4` as a searchable field, so "all logs for project 4" becomes a query. The string isn't even built if the level is switched off.
- **`NullLogger<ProjectService>.Instance`**: a logger that writes nothing. The constructor parameter is optional, so the playground demos and future unit tests can create a `ProjectService` without logging.
- The log calls sit **after** the `lock` blocks, so other requests never wait for logging. That's the "keep critical sections short" rule from Topic 4.
- Topic 17 goes further: correlation ids, scopes, what never to log (secrets, personal data).

## 6. BUILD: what changed and why

### `Program.cs`, now in two clearly separated parts
1. **Register services** (`builder.Services...`): what can be injected, and how long it lives.
2. **Build the pipeline** (`app.Use...`, `app.Map...`): which middleware runs, in which order.

```csharp
builder.Services.AddSingleton<IProjectService>(serviceProvider =>
{
    var options = serviceProvider.GetRequiredService<IOptions<ProjectStoreOptions>>().Value;
    var logger = serviceProvider.GetRequiredService<ILogger<ProjectService>>();
    return new ProjectService(SampleData.CreateProjects(), TimeSpan.FromMilliseconds(options.SimulatedLatencyMs), logger);
});
```
- **Why a factory** (`serviceProvider => ...`) instead of `AddSingleton<IProjectService, ProjectService>()`: `ProjectService` takes a `List<Project>` and a `TimeSpan`, which aren't registered services. The factory asks the container for the options and the logger (`GetRequiredService`), then calls the constructor itself.
- **Trade-off:** we could make `ProjectService` take `IOptions<ProjectStoreOptions>` directly. That ties the service to ASP.NET's options system, and every demo and test would need to build an `IOptions`. Keeping the constructor plain (`TimeSpan`) and adapting in `Program.cs` keeps the service easy to create anywhere.
- It runs **once**, the first time someone needs an `IProjectService` (singleton).

### Lifetimes lab (`Labs/Lifetimes/`)
- `OperationBase` gets an 8-character random `Id` when created. `SingletonOperation`, `ScopedOperation` and `TransientOperation` are the same class registered with three different lifetimes.
- `LifetimeReporter` (scoped) is a **second consumer** in the same request: without it you couldn't see that scoped is shared *within* a request while transient isn't.
- `LifetimesController` returns both sets of ids. It's lab code, kept small on purpose.

### `ProjectService`
- New optional `ILogger<ProjectService>? logger = null` (`NullLogger` when absent).
- Logs for create, update, delete and add-task, written after the lock.

---

## 7. Try it

1. `git pull`, start the API (**http** profile), and look at the console: one line per request from the timing middleware.
2. In `ProjectHub.Api.http`, send the **lifetimes** request **twice** and compare the ids with the table in section 2.
3. Send `GET /api/projects` and look at the `X-Response-Time-Ms` response header (about 50 in Development).
4. Change `SimulatedLatencyMs` in `appsettings.Development.json` to `300`, restart, and send it again.

## 8. DEBUG (Rider)

1. **See when objects are created:** put a breakpoint on the line `public string Id { get; } = Guid.NewGuid()...` in `OperationBase.cs`. Debug, and send the lifetimes request:
   - How many times does it stop for the **first** request, and for which types? (Look at `this` in Variables.)
   - How many times for the **second** request? Which type is *not* created again, and why?
   - In **Frames**, who calls the constructor? (Hint: it's not your code. Framework frames are often collapsed as "external code" by default; expand them, or turn off Just My Code in the debugger settings, and look for `Microsoft.Extensions.DependencyInjection`.)
2. **See the onion:** remove that breakpoint. Put breakpoints in `RequestTimingMiddleware.InvokeAsync` on `await next(context);` **and** on the `logger.LogInformation` line, and one in `ProjectsController.GetAll`. Send `GET /api/projects`. In which order are the three hit? What does that tell you about "before" and "after" `next`?
3. **Break it 1 (captive dependency):** in `Program.cs`, change `AddScoped<LifetimeReporter>()` to `AddSingleton<LifetimeReporter>()`. Start the app. What happens, and what does the message say? Then undo.
4. **Break it 2 (fail fast config):** set `"SimulatedLatencyMs": -1` in `appsettings.Development.json`. Start the app. What happens? Then undo.

## 9. CHECK: answer these in your own words

1. What is dependency injection, and what problem does it solve? (Name two benefits.)
2. **Singleton vs Scoped vs Transient:** explain each in one sentence, and say what the lab output proves.
3. Why is `ProjectService` a singleton now, and why will it become Scoped in Topic 10?
4. What is a captive dependency? Give an example, and say what ASP.NET does about it in Development.
5. What is middleware? How is it like Express middleware? Why does the order matter?
6. Why does the timing middleware set its header in `OnStarting` instead of after `await next(context)`?
7. Where do configuration values come from, and which wins? How do you override `ProjectStore:SimulatedLatencyMs` with an environment variable?
8. What do the Options pattern and `ValidateOnStart` give you?
9. Why use `"Created project {ProjectId}"` instead of `$"Created project {id}"` in a log call?
10. What does the `T` in `ILogger<T>` do? How do log levels and `Logging:LogLevel` work together?
