"""Study book for Topic 7: Dependency injection, middleware, configuration, ILogger.

Usage (from repo root):
  python3 scripts/studybooks/07-di-middleware-config-logging.py docs/studybooks/07-di-middleware-config-logging.pdf
Source code is read from git at TOPIC_REV; real runs from docs/studybooks/notes/07-runs.txt.
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

OUT = sys.argv[1]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOPIC_REV = "c7a1233"   # last code change of topic 7
NOTES = os.path.join(ROOT, "docs/studybooks/notes")


def src(rel):
    return git_show(ROOT, TOPIC_REV, rel)


def wrapped(text, width=92):
    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, width, subsequent_indent="    ") or [""])
    return "\n".join(lines)


PROGRAM = src("src/ProjectHub.Api/Program.cs")
SERVICE = src("src/ProjectHub.Api/Services/ProjectService.cs")

S = Story()

# ---------------------------------------------------------------- COVER
S += cover("Study book", "Topic 7: DI, middleware, configuration, ILogger",
           "ProjectHub learning track: React/TypeScript to C#/.NET backend. Week 2, topic 7 of 20.")
S += NOTE([
    "**What this lesson is about.** How an ASP.NET Core app is wired: **dependency injection** (the container, registrations, "
    "**Singleton vs Scoped vs Transient**, captive dependencies), the **middleware pipeline** (our own request-timing middleware), "
    "**configuration** (appsettings, environments, environment variables, the Options pattern, fail-fast validation) and **structured logging** with `ILogger`.",
    "**What we built.** `ProjectStoreOptions` (simulated latency as a setting), `RequestTimingMiddleware` (header + one log line per request), "
    "`ILogger` in `ProjectService`, a factory registration in `Program.cs`, and the **lifetimes lab** `GET /api/labs/lifetimes`.",
    "**Checkpoint:** explain Scoped vs Transient vs Singleton — proven with real ids from the lab, run by you and in the cloud.",
    "**Your questions** shaped this book: composition, how controllers are discovered, generic type arguments, the container itself, "
    "anonymous objects, and a debugger puzzle (6 breakpoint stops) where you were right and I was wrong.",
], "Brief overview")
S += H2("Contents")
S += TABLE([
    ["Part", "What is inside"],
    ["1", "DI: what, why, the container (your question), composition vs inheritance (your question)"],
    ["2", "Registering and resolving: two registration styles, the container-created rule, generics as configuration"],
    ["3", "The three lifetimes (the checkpoint), the lab, captive dependencies"],
    ["4", "Middleware: the pipeline, our timing middleware, OnStarting, order"],
    ["5", "Controller discovery: AddControllers + MapControllers (your question)"],
    ["6", "Configuration: sources and precedence, Options pattern, fail fast"],
    ["7", "ILogger: categories, levels, message templates"],
    ["8", "Our code: Program.cs, ProjectService, the lab, anonymous objects (your question)"],
    ["9", "Real runs: lifetimes, logs, headers, env var override, bad config, captive dependency"],
    ["10", "Debugging: the 6-stops puzzle, creations vs reads, breaking the rules"],
    ["11", "Your answers, corrections, interview Q&A"],
    ["12", "Summary, cheat sheet, checklist, what comes next"],
], [20, 150])
S += PageBreak()

# ---------------------------------------------------------------- PART 1
S += H1("Part 1. Dependency injection")
S += H2("1.1 What and why")
S += CODE("""
// WITHOUT DI: the class creates what it needs (hard-wired)
public class ProjectsController
{
    private readonly ProjectService _projects = new ProjectService(SampleData.CreateProjects(), ...);
}

// WITH DI: the class only DECLARES what it needs; someone else provides it
public class ProjectsController(IProjectService projects) : ControllerBase
""")
S += bullets([
    "Without DI the controller decides the concrete class, its constructor arguments and its lifetime; you cannot swap it, fake it in a test, or share one store.",
    "With DI: **registration** once in `Program.cs` (the **composition root**), **resolution** by the container when an object is needed: **constructor injection**, **inversion of control**.",
    "**Benefits (name two in the interview):** swap implementations (in-memory -> EF Core in topic 10 with one line), fakes in tests (topic 13), lifetimes managed in one place.",
])
S += H2("1.2 What IS the container? (your question)")
S += P("You asked: 'container is what? Program? passes them into its constructor — what, where? All I see is we declare in Program and then just have them in constructors of deeply nested classes.'")
S += numbered([
    "**Program.cs = the recipe book.** `builder.Services.AddScoped<LifetimeReporter>()` writes a recipe; nothing is created yet.",
    "**`builder.Build()` turns the recipes into the container**: a `ServiceProvider` object in memory inside the running app. "
    "The `serviceProvider` in the factory registration **is** the container; `GetRequiredService<...>()` asks it by hand.",
    "**A request arrives.** ASP.NET asks the container for a `LifetimesController`. The container reads the constructor, creates or reuses each dependency "
    "(recursively) and **calls the constructor itself** with them as arguments.",
])
S += CODE("""
// what the container does internally, roughly
var singleton = existingSingleton ?? new SingletonOperation();     // recipe: reuse
var scoped    = thisRequestsScoped ?? new ScopedOperation();       // recipe: one per request
var reporter  = new LifetimeReporter(singleton, scoped, new TransientOperation());
var controller = new LifetimesController(singleton, scoped, new TransientOperation(), reporter);
""")
S += OK(["Your observation was exactly right: **declare in Program.cs, then just have them in constructors of deeply nested classes.** "
         "The container is the invisible thing in between that writes every `new` for you. React analogy: a `<Provider>` at the top + `useContext()` deep inside — "
         "but the container also **creates** the objects and decides **how long they live**."])
S += H2("1.3 Composition vs inheritance (your question)")
S += P("You asked whether composition is 'anti-inheritance, so like independent'. Not quite: it is **another way to reuse code**.")
S += TABLE([
    ["", "Inheritance", "Composition"],
    ["Relationship", "**is-a**: a ProjectsController *is a* ControllerBase", "**has-a**: a ProjectsController *has an* IProjectService"],
    ["How you get behaviour", "become a subtype, inherit methods", "hold another object (field / constructor parameter) and call it"],
    ["Syntax", "`class X : BaseClass`", "`class X(IDependency dep)` then `dep.DoSomething()`"],
], [30, 70, 70])
S += bullets([
    "**React chose composition** ('Composition vs Inheritance' in the React docs): components built out of components, children, props, hooks — never `extends Button`.",
    "Our code: `ProjectsController(IProjectService projects) : ControllerBase` (has-a + is-a); `ProjectService` has a List, a Lock, an ILogger; "
    "`LoggingProjectService` wraps an inner `IProjectService` (decorator = composition).",
    "**Why prefer it:** swappable parts (DI, EF, fakes), only one base class in C#, no fragile base class, small focused classes instead of deep hierarchies.",
    "**'Independent' is partly right:** the parts are **loosely coupled** (the controller doesn't know which implementation it holds) but it still **depends** on the part's interface — DI plugs it in.",
    "Inheritance stays normal for framework base classes (`ControllerBase`, `Exception`) and real is-a families.",
])

# ---------------------------------------------------------------- PART 2
S += H1("Part 2. Registering and resolving")
S += P("Your summary: 'to make DI work we register it in Program.cs, then we can use it in a constructor — not just in a controller, in any class.' Right, with one condition:")
S += WARN(["**Only classes the container creates get injection.** Controllers (created by ASP.NET), middleware, and other registered services. "
           "If **you** write `new LifetimeReporter(...)`, there is no DI: you pass all arguments yourself — exactly what the playground demos do with `new ProjectService(...)`. "
           "Rule: in app code, don't `new` services; ask for them in the constructor."], "The condition")
S += TABLE([
    ["Style", "Example", "When"],
    ["**By type**: the container calls the constructor and resolves each parameter", "`AddScoped<LifetimeReporter>()`", "all constructor parameters are registered services"],
    ["**Factory**: you write the `new`", "`AddSingleton<IProjectService>(sp => new ProjectService(...))`", "the constructor needs non-services (`List<Project>`, `TimeSpan`)"],
    ["**Interface -> class** (everyday form)", "`AddScoped<IProjectService, ProjectService>()`", "whoever asks for the interface gets that class (topic 10)"],
], [62, 60, 48])
S += P("Forgotten registration: `Unable to resolve service for type 'X' while attempting to activate 'Y'` (checked at startup in Development).")
S += H2("2.1 A class as a generic argument (your observation)")
S += P("`app.UseMiddleware<RequestTimingMiddleware>()` works because C# generics are **reified** (topic 3): the method uses `typeof(T)` at runtime, finds the constructor, "
       "asks DI for the parameters, creates the object and calls `InvokeAsync` per request. TS generics are erased, so TS libraries pass **the class as a value** "
       "(`app.use(new X(...))`, NestJS/Inversify class tokens). C# also has `app.UseMiddleware(typeof(RequestTimingMiddleware))`; the generic form is preferred.")
S += TABLE([
    ["Code", "What the <T> tells it"],
    ["`AddSingleton<SingletonOperation>()`", "which class to register and create"],
    ["`AddOptions<ProjectStoreOptions>()`", "which class to fill from appsettings"],
    ["`GetRequiredService<ILogger<ProjectService>>()`", "which service to get from the container"],
    ["`ILogger<ProjectService>`", "the log category"],
    ["`AddSingleton<TService, TImplementation>()`", "constraint `where TImplementation : class, TService`: `AddSingleton<IProjectService, SampleData>()` does not compile"],
], [72, 98])

# ---------------------------------------------------------------- PART 3
S += PageBreak()
S += H1("Part 3. The three lifetimes (the checkpoint)")
S += TABLE([
    ["Lifetime", "Registration", "One object per...", "Typical use"],
    ["**Singleton**", "`AddSingleton<T>()`", "**application process** (until it stops)", "caches, config, our in-memory store; **must be thread-safe**"],
    ["**Scoped**", "`AddScoped<T>()`", "**HTTP request**", "EF Core `DbContext` (topic 10), per-request state"],
    ["**Transient**", "`AddTransient<T>()`", "**injection** (every time it's asked for)", "small stateless helpers"],
], [24, 36, 48, 62])
S += H2("3.1 Proof: the lifetimes lab")
S += CODE("""
request 1  controller: singleton ef200b0b  scoped 222eb6c4  transient 08a150dd
           reporter:   singleton ef200b0b  scoped 222eb6c4  transient ace29ac3
request 2  controller: singleton ef200b0b  scoped 34f8a033  transient 69a01101
           reporter:   singleton ef200b0b  scoped 34f8a033  transient 9d9ee21f
""", "Cloud run (you ran it yourself too, two requests in one session):")
S += TABLE([
    ["Lifetime", "Same within a request?", "Same across requests?", "Evidence"],
    ["Singleton", "yes", "**yes**", "`ef200b0b` everywhere"],
    ["Scoped", "**yes**", "no", "`222eb6c4` twice, then `34f8a033`"],
    ["Transient", "**no**", "no", "4 different ids"],
], [26, 40, 40, 64])
S += OK(["Your words: 'singleton same during the run/debug session; scoped per request; transient always unique, just in a scope of a class or something'.",
         "Precisions: singleton = lifetime of the **process** (restart -> new id; also why the in-memory projects reset on restart). "
         "Transient = **per injection**, not per class: a class asking twice gets two objects.",
         "Interview lines: **Singleton: one object for the whole app. Scoped: one per HTTP request. Transient: a new one every time it is injected.**"], "Your conclusion")
S += H2("3.2 How to choose")
S += bullets([
    "**Scoped** for app services that use a `DbContext` (topic 10): a service can't outlive what it holds.",
    "**Singleton** only for truly shared, **thread-safe** things. `ProjectService` is a singleton because it *is* the in-memory store (topic 4's lock makes it safe); in topic 10 it becomes **Scoped** because it will use a `DbContext` per request.",
    "**Transient** for light stateless helpers.",
])
S += H2("3.3 Captive dependencies: the rule you must not break")
S += P("**A service may only depend on things that live at least as long as itself.** We registered `LifetimeReporter` as a singleton on purpose; ASP.NET refused to start:")
S += CODE("""
Some services are not able to be constructed ...
Cannot consume scoped service 'ProjectHub.Api.Labs.Lifetimes.ScopedOperation'
from singleton 'ProjectHub.Api.Labs.Lifetimes.LifetimeReporter'.
""")
S += P("You asked (debug step 3): 'what uses the reporter so it's not ok?' — it's not **who uses** it but **what it holds**: its constructor takes a `ScopedOperation`. "
       "A singleton is created once and would keep request 1's scoped object **forever**. Real life: one request's `DbContext` or 'current user' leaking into everyone's requests.")
S += TABLE([
    ["A ... may depend on a ...", "Singleton", "Scoped", "Transient"],
    ["**Singleton**", "yes", "**no (captive)**", "allowed, but lives as long as the singleton"],
    ["**Scoped**", "yes", "yes", "yes"],
    ["**Transient**", "yes", "yes", "yes"],
], [44, 30, 40, 56])
S += WARN(["Your first answer: 'singleton relies on scoped **or transient**'. Transient inside a singleton is allowed (it just lives as long as the singleton). "
           "The captive problem is singleton -> **scoped**. And say what ASP.NET does: in Development it refuses to start."])

# ---------------------------------------------------------------- PART 4
S += PageBreak()
S += H1("Part 4. Middleware")
S += CODE("""
request  -> RequestTiming -> HttpsRedirection -> Authorization -> [routing -> controller action]
response <- RequestTiming <- HttpsRedirection <- Authorization <-
""")
S += P("Each middleware can work **before** `next`, call `next` (the rest of the pipeline), work **after**, or **short-circuit** (answer without calling `next`, e.g. auth -> 401). Express: `app.use(async (req, res, next) => { ...; await next(); ... })`.")
S += CODE(src("src/ProjectHub.Api/Middleware/RequestTimingMiddleware.cs"), "src/ProjectHub.Api/Middleware/RequestTimingMiddleware.cs")
S += TABLE([
    ["Piece", "Why"],
    ["`RequestDelegate next` / `HttpContext context`", "Express's `next` / `req` + `res`"],
    ["`Response.OnStarting(...)`", "headers go out **before** the body; after `await next` the response may already have started ('response has already started'); OnStarting runs at the last moment headers can change"],
    ["`try { await next } finally { log }`", "log even if something below throws (status may still say 200 then; topic 12 fixes it)"],
    ["`app.UseMiddleware<...>()` **first**", "it measures everything after it; **order matters**: a middleware only sees what comes after it"],
    ["created once", "middleware behaves like a singleton: scoped services go into `InvokeAsync` parameters, not the constructor"],
], [56, 114])
S += P("The startup warning `Failed to determine the https port for redirect` is harmless: the http-only profile gives HTTPS redirection nowhere to redirect.", small)

# ---------------------------------------------------------------- PART 5
S += H1("Part 5. How controllers are found (your question)")
S += P("You noticed `LifetimesController` works although it is not in the `Controllers` folder. Two steps, and the folder doesn't matter:")
S += numbered([
    "**`AddControllers()` discovers** controllers by **reflection** over the compiled assembly: public, non-abstract, and (inherits `ControllerBase` OR name ends with `Controller` OR has `[Controller]`/`[ApiController]`). `Controllers/` is only a human convention.",
    "**`MapControllers()` maps** each action's `[Route]` + `[HttpGet]`... into an **endpoint** (verb + URL -> action) that routing matches.",
])
S += bullets([
    "No `MapControllers()`: every request 404. No `AddControllers()`: `MapControllers()` fails at startup asking for it.",
    "NestJS decorators (`@Controller`, `@Get`) are the same idea; Next.js is the opposite (the folder **is** the route).",
    "All discovered endpoints: `http://localhost:5064/openapi/v1.json`.",
])

# ---------------------------------------------------------------- PART 6
S += H1("Part 6. Configuration")
S += TABLE([
    ["Order (later wins)", "Source", "Note"],
    ["1", "`appsettings.json`", "defaults (ours: SimulatedLatencyMs 0)"],
    ["2", "`appsettings.{Environment}.json`", "`ASPNETCORE_ENVIRONMENT`; launchSettings sets Development (ours: 50)"],
    ["3", "user secrets", "Development only, outside the repo"],
    ["4", "**environment variables**", "`ProjectStore__SimulatedLatencyMs=500` (double underscore = nesting)"],
    ["5", "command-line arguments", ""],
], [30, 56, 84])
S += P("Secrets never go in appsettings in git: user secrets locally, Key Vault in Azure (topic 19).")
S += WARN(["Your first answer covered appsettings -> appsettings.Development.json (right) but missed that **environment variables beat both** — how servers and Azure change settings without editing files. Re-check: right."])
S += CODE(src("src/ProjectHub.Api/Configuration/ProjectStoreOptions.cs"), "src/ProjectHub.Api/Configuration/ProjectStoreOptions.cs")
S += bullets([
    "**Options pattern:** settings as a **typed class** injected as `IOptions<ProjectStoreOptions>` instead of magic strings.",
    "`BindConfiguration` (JSON -> object), `ValidateDataAnnotations` (`[Range]`), `ValidateOnStart` (**fail fast** at startup, not on a random request).",
    "Variants: `IOptions<T>` (read once), `IOptionsSnapshot<T>` (per request, scoped), `IOptionsMonitor<T>` (live changes).",
])

# ---------------------------------------------------------------- PART 7
S += H1("Part 7. ILogger")
S += bullets([
    "`ILogger<T>`: injected; `T` = the **category** (`ProjectHub.Api.Services.ProjectService`) shown on every line; levels can be set per category.",
    "**Levels:** Trace < Debug < Information < Warning < Error < Critical. `Logging:LogLevel` sets the minimum per category: `Default: Information` (our logs), `Microsoft.AspNetCore: Warning` (quiet framework).",
    "**Message templates, not interpolation:** `LogInformation(\"Created project {ProjectId}\", id)` makes `ProjectId` a **searchable field** in log systems; `$\"...\"` bakes it into text. A template isn't even formatted if the level is off.",
    "`NullLogger<ProjectService>.Instance` writes nothing: the optional constructor parameter lets demos/tests skip logging.",
    "Logs are written **after** the `lock` (topic 4: keep critical sections short).",
])
S += CODE(method(SERVICE, "public async Task<Project> CreateAsync"), "ProjectService.CreateAsync with logging:")

# ---------------------------------------------------------------- PART 8
S += PageBreak()
S += H1("Part 8. Our code")
S += CODE(PROGRAM, "src/ProjectHub.Api/Program.cs: 1. register services, 2. build the pipeline")
S += bullets([
    "**Why a factory** for `IProjectService`: the constructor needs a `List<Project>` and a `TimeSpan` (not services); the factory asks the container for the options and the logger.",
    "**Trade-off:** taking `IOptions<ProjectStoreOptions>` in the service would tie it to ASP.NET's options system; a plain `TimeSpan` keeps it easy to create anywhere (demos, tests).",
])
S += H2("8.1 The lifetimes lab")
S += CODE(src("src/ProjectHub.Api/Labs/Lifetimes/OperationBase.cs"), "OperationBase.cs (explicit constructor added after the 6-stops puzzle, Part 10)")
S += CODE(src("src/ProjectHub.Api/Labs/Lifetimes/LifetimeReporter.cs") + "\n" + src("src/ProjectHub.Api/Labs/Lifetimes/LifetimesController.cs"),
          "LifetimeReporter.cs and LifetimesController.cs")
S += H3("Anonymous objects as responses (your question)")
S += P("`controller = new { singleton = singleton.Id, ... }` creates an **anonymous type** (topic 2), like a JS object literal, nested inside the outer `new { controller = ..., reporter = ... }`. "
       "`Ok(...)` serializes it to `{\"controller\":{\"singleton\":\"ef200b0b\",...},\"reporter\":{...}}`. The compiler generates a class with read-only properties but no name you can write, "
       "so it can't be an `ActionResult<T>`. Fine for a lab; real endpoints use **record DTOs** (named contract, OpenAPI can describe it, typed frontend client, testable).")

# ---------------------------------------------------------------- PART 9
S += H1("Part 9. Real runs")
S += CODE(wrapped(open(os.path.join(NOTES, "07-runs.txt"), encoding="utf-8").read()), "Cloud container, Development profile (docs/studybooks/notes/07-runs.txt):")
S += bullets([
    "`X-Response-Time-Ms: 51` = the 50 ms Development latency. Env var 500 -> **601** (the first request also includes warm-up).",
    "`-1` -> `OptionsValidationException` at startup (exit 134). Captive dependency -> refused to start (exit 134).",
])

# ---------------------------------------------------------------- PART 10
S += PageBreak()
S += H1("Part 10. Debugging")
S += H2("10.1 The 6-stops puzzle (you were right, I was wrong)")
S += P("With a breakpoint on `public string Id { get; } = Guid.NewGuid()...` you saw **6 stops in both requests**, in one session, with correct lifetime results. "
       "I first blamed two debug sessions (the '2' on the debug icon) — **wrong**. You insisted, rightly.")
S += CODE("""
public string Id { get; } = Guid.NewGuid().ToString()[..8];
//                 └ getter ┘  └──── initializer (runs once, at creation) ────┘
""")
S += bullets([
    "That line holds the **getter** too: a breakpoint there stops on every **read** of `Id`. Reads per request: controller 3 + reporter 3 = **6**, regardless of creations.",
    "Your hypothesis ('generation is skipped when not needed') was close; precisely: the id is generated **only at creation**; the extra stops are **reads**.",
    "Proof via **Frames**: one frame down is `LifetimesController.Get` / `LifetimeReporter.Report` (a read), not the DI container (a creation).",
    "**Fix:** `OperationBase` got an explicit constructor; a breakpoint inside it counts **creations**: request 1 -> **4** (Singleton lazily on first need, Scoped once, Transient twice), request 2 -> **3** (no Singleton).",
    "Interview point: **properties are methods** (`{ get; }` compiles to `get_Id()`).",
    "Lesson for both of us: when an observation contradicts the prediction, check the prediction's assumption (what the breakpoint line actually covers) before blaming the environment.",
])
S += H2("10.2 The other steps")
S += TABLE([
    ["Step", "Result"],
    ["The middleware onion (breakpoints before/after `next` + in the controller)", "order: before `next` -> controller -> after `next`"],
    ["Break it 1: `AddSingleton<LifetimeReporter>()`", "'Some services are not able to be constructed' / 'Cannot consume scoped service ... from singleton' (you did it)"],
    ["Break it 2: `SimulatedLatencyMs: -1`", "the app didn't start: validation (you did it, right)"],
], [80, 90])

# ---------------------------------------------------------------- PART 11
S += PageBreak()
S += H1("Part 11. Your answers, corrections, interview Q&A")
S += TABLE([
    ["Question", "Your answer", "Verdict / complete answer"],
    ["1. What is DI?", "integrating a service via the constructor; composition, easier to maintain (half)", "the container creates dependencies and passes them in; benefits: swap implementations, fakes in tests, lifetimes in one place"],
    ["2. Lifetimes", "one per session/runtime; per request; per 'usage' (right)", "'usage' = injection"],
    ["3. Why singleton now / scoped later", "shared in-memory global state; DbContext per request (right)", ""],
    ["4. Captive dependency", "singleton relying on scoped **or transient** (half)", "singleton -> scoped; transient allowed; refuses to start in Development"],
    ["5. Middleware", "Express-like, next, order matters (right)", "+ before/after next, short-circuit; timing first"],
    ["6. OnStarting", "?? -> re-check: headers would be gone (right)", "headers are sent before the body"],
    ["7. Config precedence", "appsettings -> Development (half) -> re-check: env var wins (right)", "double underscore for nesting"],
    ["8. Options + ValidateOnStart", "? -> re-check: typed config + validation, app won't start with a bad value (right)", ""],
    ["9. Templates vs $\"\"", "? -> re-check: track/filter by project (right)", "searchable field"],
    ["10. ILogger<T>, levels", "?", "T = category; minimum level per category in Logging:LogLevel"],
], [36, 68, 66])
S += H2("Interview questions with model answers")
qa = [
    ("What is dependency injection?", "Classes declare dependencies in their constructor; the container creates and passes them in. Benefits: swappable implementations, testability with fakes, central lifetime management."),
    ("What is the DI container?", "A ServiceProvider built from the registrations in Program.cs (builder.Build()); at runtime it creates objects, resolves constructor chains recursively and manages lifetimes."),
    ("Singleton vs Scoped vs Transient?", "Singleton: one per application process. Scoped: one per HTTP request. Transient: a new instance on every injection."),
    ("Which lifetime for a DbContext? For an in-memory store?", "DbContext: Scoped. In-memory shared store: Singleton, and it must be thread-safe."),
    ("What is a captive dependency?", "A longer-lived service holding a shorter-lived one (singleton -> scoped), keeping it forever; ASP.NET refuses to start in Development."),
    ("Which classes get constructor injection?", "Only classes the container creates: controllers, middleware, registered services. A class you new yourself gets nothing injected."),
    ("By-type vs factory registration?", "By type: the container calls the constructor and resolves parameters. Factory: you construct it, e.g. when the constructor needs non-service values."),
    ("Composition vs inheritance?", "Inheritance is is-a (become a subtype); composition is has-a (hold and delegate). Prefer composition: swappable parts, no fragile hierarchies."),
    ("What is middleware? Why does order matter?", "Components in a pipeline that can act before/after next or short-circuit; each only sees what comes after it."),
    ("Why set a response header in OnStarting?", "Headers are sent before the body; after the action writes, it can be too late. OnStarting runs right before headers are sent."),
    ("How are controllers found?", "AddControllers discovers them by reflection (ControllerBase / Controller suffix / attributes); MapControllers maps their attribute routes to endpoints. Folders don't matter."),
    ("Configuration precedence?", "appsettings.json < appsettings.{Env}.json < user secrets (dev) < environment variables < command line. Nested env vars use __."),
    ("What is the Options pattern? ValidateOnStart?", "Typed settings classes injected as IOptions<T>; ValidateOnStart validates at startup so bad config fails fast."),
    ("Why message templates instead of interpolation in logs?", "Placeholders become structured, searchable fields; interpolation produces plain text and is formatted even when the level is off."),
    ("What does ILogger<T>'s T do?", "Sets the log category (the class name) so you can see the source and configure levels per category."),
    ("Why can a breakpoint on a property line stop many times?", "An auto-property line holds its getter; every read stops there. Properties are methods."),
]
for q, a in qa:
    S += QA(q, a)

# ---------------------------------------------------------------- PART 12
S += PageBreak()
S += H1("Part 12. Summary")
S += OK([
    "**DI:** register in Program.cs (recipes) -> `builder.Build()` creates the container -> it constructs every class it creates, resolving constructor chains.",
    "**Lifetimes:** Singleton per app process, Scoped per request, Transient per injection. Never singleton -> scoped (captive dependency).",
    "**Composition** (has-a) over inheritance (is-a) for your own code; DI plugs the parts in.",
    "**Middleware:** ordered pipeline, before/after `next`, short-circuit; headers via `OnStarting`.",
    "**Controllers** are discovered by `AddControllers` and mapped by `MapControllers`; folders don't matter.",
    "**Configuration:** JSON < environment JSON < secrets < env vars < command line; Options pattern + ValidateOnStart = typed and fail-fast.",
    "**Logging:** `ILogger<T>` categories, levels, message templates for structured logs; log outside locks.",
    "**Debugging:** a breakpoint on an auto-property line also stops on reads; count creations in a constructor.",
], "Key takeaways")
S += H2("Cheat sheet")
S += TABLE([
    ["Need", "Code"],
    ["one shared instance", "`builder.Services.AddSingleton<IFoo, Foo>();`"],
    ["one per request", "`builder.Services.AddScoped<IFoo, Foo>();`"],
    ["new every time", "`builder.Services.AddTransient<IFoo, Foo>();`"],
    ["custom construction", "`builder.Services.AddSingleton<IFoo>(sp => new Foo(sp.GetRequiredService<IBar>(), 42));`"],
    ["use it", "`public class X(IFoo foo)` (constructor injection)"],
    ["typed settings", "`AddOptions<T>().BindConfiguration(\"Section\").ValidateDataAnnotations().ValidateOnStart();` + inject `IOptions<T>`"],
    ["override a setting", "`Section__Key=value` environment variable"],
    ["middleware", "`app.UseMiddleware<MyMiddleware>();` (class with `InvokeAsync(HttpContext)` + `RequestDelegate next`)"],
    ["log", "`logger.LogInformation(\"Did {Thing} for {Id}\", thing, id);`"],
], [40, 130])
S += H2("Checklist: can you do this without notes?")
S += bullets([
    "Explain what the container is and how it builds `LifetimesController`.",
    "Explain the three lifetimes with the lab output, and the captive-dependency rule with an example.",
    "Explain why only container-created classes get injection.",
    "Explain composition vs inheritance with ProjectHub examples.",
    "Explain middleware order and why `OnStarting` is needed for headers.",
    "Explain configuration precedence and how to override a setting with an env var.",
    "Explain message templates vs interpolation in logs.",
])
S += H2("What comes next: Topic 8 (SQL basics)")
S += P("SQL Server in Docker, the ProjectHub tables created **by hand** (primary and foreign keys), and ten queries (SELECT, WHERE, ORDER BY, INSERT, UPDATE, DELETE). "
       "Checkpoint: query and change data without EF Core.")

build(OUT, S, "ProjectHub study book | Topic 7: DI, middleware, configuration, ILogger", "ProjectHub study book: Topic 7, DI, middleware, configuration, logging")
print("ok", OUT)
