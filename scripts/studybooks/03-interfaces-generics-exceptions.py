"""Study book for Topic 3: Interfaces, generics, exceptions.

Usage (from repo root):
  python3 scripts/studybooks/03-interfaces-generics-exceptions.py docs/studybooks/03-interfaces-generics-exceptions.pdf [demo-output.txt]
Source files are read from src/ so the printed code always matches the repo.
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

OUT = sys.argv[1]
DEMO_OUT = sys.argv[2] if len(sys.argv) > 2 else None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def wrap_output(text, width=92):
    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, width, subsequent_indent="    ") or [""])
    return lines


S = Story()

# ---------------------------------------------------------------- COVER
S += cover("Study book", "Topic 3: Interfaces, generics, exceptions",
           "ProjectHub learning track: React/TypeScript to C#/.NET backend. Week 1, topic 3 of 20.")
S += NOTE([
    "**What this lesson is about.** How C# separates a **contract** (an interface) from an **implementation** (a class), why code should depend "
    "on the contract, how to write your own **generics** (generic methods, constraints, generic types), and how to design **exceptions**: "
    "expected vs unexpected errors, custom exception types, `null` vs throwing, `throw;` vs `throw ex;`.",
    "**What we built.** The first real backend layer: `IProjectService` + `ProjectService` (in-memory, with a business rule: unique project names), "
    "two exception types (`NotFoundException`, `BusinessRuleException`), and a 10-section demo. In Rider you used a **.NET exception breakpoint** "
    "to stop exactly where an exception is thrown.",
    "**Why it matters for the interview.** 'Interface vs class / abstract class', 'why program against an interface', 'expected vs unexpected errors', "
    "'throw vs throw ex', and 'why constructor injection' are standard .NET interview questions. Topics 6, 7, 10, 12 and 13 all build on this code.",
], "Brief overview")
S += H2("Contents")
S += TABLE([
    ["Part", "What is inside"],
    ["1", "Interfaces: contract vs implementation, nominal matching, why program against the interface, interface vs abstract class"],
    ["2", "Generics: generic methods and types, constraints, reified generics vs TS"],
    ["3", "Exceptions: try/catch/finally in C#, catch order, when filters, throw; vs throw ex;, expected vs unexpected, null vs throw"],
    ["4", "Our code: exceptions, IProjectService, ProjectService (with the constructor explained), design decisions, known limitations"],
    ["5", "`var` vs an explicit (interface) type: your question"],
    ["6", "The demo: 10 sections and full output"],
    ["7", "Debugging in Rider: .NET exception breakpoints, reading the Variables panel, unhandled exceptions"],
    ["8", "Your answers, corrections, and interview Q&A with model answers"],
    ["9", "Summary, cheat sheet, checklist, what comes next"],
], [20, 150])
S += PageBreak()

# ---------------------------------------------------------------- PART 1
S += H1("Part 1. Interfaces")
S += P("An interface is a **contract**: a list of members (methods, properties) **without implementation**. A class that implements it promises to provide all of them; "
       "if one is missing, the build fails.")
S += CODE("""
public interface IProjectService
{
    Project? GetById(int id);
}

public class ProjectService : IProjectService   // ": IProjectService" = "I implement this contract"
{
    public Project? GetById(int id) => ...;     // must exist, or the build fails
}
""")
S += H2("1.1 The big difference from TypeScript")
S += TABLE([
    ["", "TypeScript `interface`", "C# `interface`"],
    ["How a class matches", "**structurally**: any object with the right shape fits", "**nominally**: the class must **declare** `: IProjectService`; the compiler checks every member"],
    ["Exists at runtime?", "no, erased", "yes: `service is IProjectService` works"],
    ["Describes data shapes?", "very often (`interface User { name: string }`)", "rarely; data shapes are classes/records. Interfaces describe **behavior**"],
    ["Naming", "`User`, `ProjectService`", "`I` prefix: `IProjectService`, `IEnumerable<T>`"],
], [36, 62, 72])
S += H2("1.2 Program against the interface")
S += CODE("""
IProjectService service = new ProjectService(data);             // variable typed as the CONTRACT
static void PrintProjectCount(IProjectService service) { ... }  // works with ANY implementation
""")
S += P("A variable typed as the interface can only use what the interface describes, even if the class has more public members (your own observation in the quiz). Benefits:")
S += numbered([
    "**Swap implementations.** Today an in-memory list; in topic 10 EF Core + SQL Server. Code that only knows `IProjectService` does not change.",
    "**Testing (topics 13-14).** A test passes a fake implementation, so a controller can be tested without a database.",
    "**Dependency injection (topic 7).** ASP.NET is configured to hand out `ProjectService` whenever someone asks for `IProjectService`.",
    "**Decorators (demo section 7).** `LoggingProjectService` implements the same interface, wraps another implementation, adds logging; callers cannot tell the difference.",
])
S += P("This is **polymorphism**: one interface, many implementations, chosen at runtime.")
S += H2("1.3 Interface vs abstract class vs class")
S += TABLE([
    ["", "`interface`", "`abstract class`", "`class`"],
    ["Implementation?", "no (rare default methods aside)", "partly: some members implemented, some `abstract`", "fully"],
    ["Fields / state?", "no", "yes", "yes"],
    ["Can you `new` it?", "no", "no", "yes"],
    ["How many per class?", "**many**: `class X : IA, IB, IC`", "**one** base class", "**one** base class"],
    ["Use for", "a contract or capability ('can do X')", "shared base code for closely related types", "the actual implementation"],
], [32, 46, 50, 42])
S += P("Modern .NET favors interfaces and **composition over inheritance**: `LoggingProjectService` *contains* another service instead of *inheriting* from one. "
       "The everyday exception to 'little inheritance': custom exceptions inherit from `Exception` (Part 4).")

# ---------------------------------------------------------------- PART 2
S += H1("Part 2. Generics")
S += P("You have used generics since topic 1 (`List<T>`, `Dictionary<TKey, TValue>`, `Func<T, bool>`). A generic has a **type parameter** `T` that the caller fills in, like TS generics.")
S += CODE("""
// generic METHOD: T is inferred from the argument
static T Largest<T>(IEnumerable<T> items) where T : IComparable<T> { ... }
Largest(new[] { 3, 9, 4 });            // T = int     -> 9
Largest(new[] { "pear", "apple" });    // T = string  -> "pear"

// generic TYPE
record Page<T>(IReadOnlyList<T> Items, int PageNumber, int TotalCount);
Page<string> names = ...;   Page<TaskItem> tasks = ...;
""")
S += H2("2.1 Constraints: where T : ... (TS: T extends ...)")
S += P("Without a constraint you can only do with `T` what works for every type. A constraint unlocks more:")
S += TABLE([
    ["Constraint", "Meaning", "Example"],
    ["`where T : IComparable<T>`", "T can be compared: `CompareTo` exists", "`Largest<T>` in the demo"],
    ["`where T : class`", "reference type", "makes `T?` mean 'nullable reference'"],
    ["`where T : struct`", "value type", "`Nullable<T>` is declared like this"],
    ["`where T : new()`", "has a public parameterless constructor", "`new T()` inside the method"],
    ["`where T : BaseClass` / `IInterface`", "is or implements it", "use its members"],
    ["`where T : notnull`", "not nullable", "dictionary keys"],
], [52, 60, 58])
S += P("`Largest(service.GetAll())` does **not compile**: `Project` does not implement `IComparable<Project>`, so the constraint rejects it at compile time.")
S += H2("2.2 C# generics exist at runtime (unlike TS)")
S += P("TS generics are **erased**: at runtime there is only `Array`. C# generics are **reified**: `List<int>` and `List<string>` are different runtime types, "
       "`typeof(T)` works inside a generic method, and `List<int>` stores real `int`s (no boxing).")

# ---------------------------------------------------------------- PART 3
S += H1("Part 3. Exceptions")
S += TABLE([
    ["Feature", "C#", "JS"],
    ["Catch by type", "`catch (NotFoundException ex) { }` then `catch (Exception ex) { }`", "one `catch (e)` + `instanceof` checks"],
    ["Catch order", "most specific **first**; general before specific = **compile error**", "n/a"],
    ["Filters", "`catch (NotFoundException ex) when (ex.Key is int id && id > 10)`", "n/a"],
    ["Rethrow", "`throw;` keeps the original stack trace", "`throw e`"],
    ["What can be thrown", "only `Exception` objects (or subclasses)", "anything, even strings"],
    ["`finally`", "always runs: success, caught, or still flying", "same"],
], [30, 82, 58])
S += H2("3.1 throw; vs throw ex;")
S += CODE("""
throw;    -> top frame: ThrowDeepInside()   <- where the error REALLY happened
throw ex; -> top frame: Rethrow(...)        <- original location LOST
""", "Demo section 6 output (shortened):")
S += P("`throw ex;` **resets the stack trace** to the current line, so logs and debugging lose where the bug was. Always rethrow with `throw;` (compiler warning CA2200). "
       "Names like `<<Main>$>g__ThrowDeepInside|0_6` are compiler-generated names for local functions: read the method name inside.")
S += H2("3.2 Expected vs unexpected errors")
S += TABLE([
    ["", "Expected error", "Unexpected error (bug / infrastructure)"],
    ["ProjectHub examples", "duplicate project name, empty title, project id does not exist", "`SingleOrDefault` with two projects sharing an Id (`InvalidOperationException`); `Create(null!, ...)` -> `NullReferenceException` on `Trim`; `Max()` on empty without `DefaultIfEmpty`; database down (later)"],
    ["Whose fault", "the **caller's input**", "**our code** or the environment"],
    ["What to do", "catch where you can turn it into an answer for the user: HTTP **4xx**", "do **not** catch locally; a global handler logs it and returns HTTP **500** (topic 12)"],
    ["Type", "`BusinessRuleException`, `NotFoundException`", "whatever .NET throws"],
], [30, 62, 78])
S += bullets([
    "**Catch only what you can handle.** Catching `Exception` everywhere hides bugs; never write an empty `catch { }`.",
    "**Do not use exceptions for normal control flow.** If 'not found' is ordinary, return `null` or use the **Try pattern** (`TryGetValue`, `int.TryParse`).",
    "**Custom types carry meaning and data**: catch by type; map type -> HTTP status; `ex.EntityName`, `ex.Key`.",
    "`finally` / `using var x = ...;` for cleanup (files, DB connections).",
])
S += H2("3.3 null vs exception: query vs command")
S += TABLE([
    ["Method", "Behaviour", "Design reason"],
    ["`GetById(id)`", "returns `Project?` (null when missing)", "a **query**: 'is there a project 99?' 'No' is a valid answer; the caller decides"],
    ["`AddTask(projectId, ...)`", "throws `NotFoundException`", "a **command** that **cannot be carried out**; returning null would let the caller continue as if it worked"],
], [36, 52, 82])

# ---------------------------------------------------------------- PART 4
S += PageBreak()
S += H1("Part 4. Our code, explained")
S += H2("4.1 The exceptions")
S += CODE(src("src/ProjectHub.Api/Exceptions/NotFoundException.cs"), "src/ProjectHub.Api/Exceptions/NotFoundException.cs")
S += CODE(src("src/ProjectHub.Api/Exceptions/BusinessRuleException.cs"), "src/ProjectHub.Api/Exceptions/BusinessRuleException.cs")
S += bullets([
    "`: Exception(...)`: inherits from `System.Exception` and passes the message to the base constructor, like `super(message)` in `class MyError extends Error`.",
    "**Primary constructor** `class NotFoundException(string entityName, object key)`: parameters on the class line (C# 12+), short for a constructor that receives them. "
    "`EntityName { get; } = entityName` stores one in a read-only property.",
    "`object key`: `object` is the base type of everything (like `unknown`): ids may be `int` today and `Guid` later.",
    "Not named `ValidationException` because `System.ComponentModel.DataAnnotations.ValidationException` already exists and ASP.NET uses it.",
])
S += H2("4.2 The contract: IProjectService")
S += CODE(src("src/ProjectHub.Api/Services/IProjectService.cs"), "src/ProjectHub.Api/Services/IProjectService.cs")
S += P("Return types are part of the contract: `IReadOnlyList<Project>` = 'read, do not change the list'; `Project?` = 'may be null, check it'. "
       "C# has no `throws` clause (unlike Java), so comments document which exceptions each method throws.")
S += H2("4.3 The implementation: ProjectService")
S += CODE(src("src/ProjectHub.Api/Services/ProjectService.cs"), "src/ProjectHub.Api/Services/ProjectService.cs")

S += H2("4.4 The constructor of ProjectService (your request)")
S += NOTE([
    "This block is the **constructor** of `public class ProjectService : IProjectService`:",
    CODE("""
public ProjectService(IEnumerable<Project> initialProjects)   // <- CONSTRUCTOR
{
    _projects = initialProjects.ToList();

    // DefaultIfEmpty(0): Max() on an empty sequence would throw (Topic 2 gotcha).
    _nextProjectId = _projects.Select(p => p.Id).DefaultIfEmpty(0).Max() + 1;
    _nextTaskId = _projects.SelectMany(p => p.Tasks).Select(t => t.Id).DefaultIfEmpty(0).Max() + 1;
}
""", width_mm=153)[0],
    "**How to recognize it:** same name as the class and **no return type** (no `void`, no `Project`). Only a constructor looks like that.",
    "**When it runs:** once per object, on `new ProjectService(data)`. Its job is to set up the starting state: copy the data, compute the next ids.",
    "**TS equivalent:** `constructor(initialProjects: Iterable<Project>) { this.projects = [...initialProjects]; ... }`.",
    "**C#-specific:** `readonly` fields (`_projects`) can be assigned **only here** (or in their declaration); after that they are locked.",
    "**Two constructor styles you have seen:** classic (this one: a member inside the class body) and **primary** (the exceptions: `class NotFoundException(string entityName, object key)`). Same concept, different syntax.",
], "The constructor")
S += H3("Why the data comes in through the constructor (constructor injection)")
S += bullets([
    "If the service called `SampleData.CreateProjects()` itself, the dependency would be **hidden and hard-coded**.",
    "Passing it in: **tests choose the data** (empty list, a project named X then create X again), and the **source is swappable** without editing the service.",
    "This is **dependency injection** in its simplest form; topic 7 lets ASP.NET do it automatically.",
    "TS analogy: a class that `import`s a module singleton inside itself (testing needs `jest.mock`) vs a class that receives the dependency in its constructor (pass a fake).",
])
S += H2("4.5 Line by line")
S += TABLE([
    ["Line", "Why"],
    ["`public class ProjectService : IProjectService`", "implements the contract; compiler checks every member"],
    ["`private readonly List<Project> _projects`", "`readonly`: the field cannot be reassigned after the constructor (list contents still can). `_camelCase` = private field"],
    ["`_projects = initialProjects.ToList()`", "own copy; enumerate once (topic 2); caller's later changes do not affect it"],
    ["`.Select(p => p.Id).DefaultIfEmpty(0).Max() + 1`", "next id; `DefaultIfEmpty(0)` avoids Max-on-empty (topic 2)"],
    ["`public const int MaxNameLength = 100;`", "compile-time constant, reusable by the API layer later"],
    ["`GetAll() => _projects.AsReadOnly()`", "read-only wrapper; cast + `Add` throws `NotSupportedException` (demo 8)"],
    ["`GetById(...) => _projects.SingleOrDefault(...)`", "`Single`: ids must be unique; a duplicate is a bug worth surfacing"],
    ["`name.Trim()`", "`\"  Docs portal  \"` and `\"Docs portal\"` are the same name"],
    ["three `if ... throw new BusinessRuleException(...)`", "**guard clauses**: check and exit early; the happy path stays flat"],
    ["`string.Equals(a, b, StringComparison.OrdinalIgnoreCase)`", "**the business rule** (unique names, ignoring case). Better than `ToLower()`: no new strings, no dependence on server **culture** (Turkish 'i')"],
    ["`Id = _nextProjectId++`", "use the current value, then increment"],
    ["`GetById(projectId) ?? throw new NotFoundException(...)`", "**throw expression**: get it or throw"],
    ["`nameof(Project)`", "the string \"Project\", checked by the compiler; follows renames"],
], [74, 96])
S += H2("4.6 Known limitations (on purpose)")
S += numbered([
    "**Not thread-safe.** Two simultaneous requests could get the same id or corrupt the list. Addressed when the service is shared across requests (topics 6-7); EF Core makes the database handle ids (topic 10).",
    "**Entities leak.** `GetAll()` is read-only as a list, but the `Project` objects inside are mutable: demo section 8 renames a project from outside. Topic 6 fixes it with **DTOs** (the API returns copies, never entities).",
])

# ---------------------------------------------------------------- PART 5
S += H1("Part 5. var vs an explicit (interface) type (your question)")
S += P("You asked: in `IReadOnlyList<Project> all = service.GetAll();` can I write `var all = service.GetAll();`? You tried it and it works, and you prefer `var`.")
S += bullets([
    "**Here it is identical.** `GetAll()` already returns `IReadOnlyList<Project>`, so `var` infers exactly that (hover in Rider to see it). The explicit type in demo section 8 was for teaching: the section is *about* the type.",
    "**Where it is NOT just style** (demo section 1):",
])
S += CODE("""
IProjectService service = new ProjectService(data);   // type: IProjectService (only the contract is visible)
var service             = new ProjectService(data);   // type: ProjectService  (the concrete class)
""")
S += P("`var` infers from the right side, which is the concrete class. Writing the interface type is a deliberate choice: 'this code depends only on the contract'. "
       "In real ASP.NET code you rarely write this line, because DI (topic 7) hands you an `IProjectService`.")
S += OK(["Rule: `var` when the right side already has the type you want; an explicit type when you want a **different, usually more general** type (the interface instead of the class). Preferring `var` is a fine habit."])

# ---------------------------------------------------------------- PART 6
S += H1("Part 6. The demo: playground/03-services-exceptions.cs")
S += P("Run from the repo root: `dotnet run playground/03-services-exceptions.cs`. It is also listed in the `playground` solution folder in Rider.")
S += TABLE([
    ["#", "Section", "Shows"],
    ["1", "Program against the interface", "variable typed `IProjectService`; `GetById(99)` returns null"],
    ["2", "Happy path", "`Create` trims the name; `AddTask` gets default status `Todo`"],
    ["3", "The business rule", "duplicate (different case), empty, too long -> `BusinessRuleException`"],
    ["4", "NotFoundException", "carries `EntityName` and `Key`, not only a message"],
    ["5", "catch order, `when`, `finally`", "specific before general; filter; finally always runs"],
    ["6", "`throw;` vs `throw ex;`", "which stack trace survives"],
    ["7", "Polymorphism + decorator", "`LoggingProjectService` wraps any `IProjectService`; calling code unchanged"],
    ["8", "Encapsulation", "read-only list (cast + Add throws) vs mutable entities (the leak)"],
    ["9", "Generic method + constraint", "`Largest<T>` with int, string, DateTime"],
    ["10", "Generic type", "`Page<T>` for strings and tasks"],
], [10, 56, 104])
if DEMO_OUT and os.path.exists(DEMO_OUT):
    S += H3("Full output (captured in the cloud container)")
    lines = wrap_output(open(DEMO_OUT, encoding="utf-8").read())
    for i in range(0, len(lines), 45):
        S += CODE("\n".join(lines[i:i + 45]))
S += P("Note: section 9's `DateTime` result and the 'Renamed by a caller!' name in section 10 come from earlier sections changing data (section 2 created a project today; section 8 renamed project 1).", small)

# ---------------------------------------------------------------- PART 7
S += PageBreak()
S += H1("Part 7. Debugging: stop where an exception is thrown")
S += P("A caught exception is invisible: the program just continues. A **.NET exception breakpoint** makes Rider stop at the `throw` line anyway.")
S += H2("7.1 Steps")
S += numbered([
    "Paste the snippet below into `Program.cs` right before `app.Run();`.",
    "Debug once with no breakpoints: it does not stop (the exception is caught; only the console line appears).",
    "Add an exception breakpoint: **Run > View Breakpoints... > + > .NET Exception Breakpoint**, type `BusinessRuleException`, OK.",
    "Debug again: Rider stops **inside `ProjectService.Create`, on the `throw` line**, although the exception will be caught.",
    "Inspect the Variables panel (and Frames).",
    "Break it: remove the `try/catch` and debug again.",
    "Clean up: delete the snippet and the exception breakpoint.",
])
S += CODE("""
var debugService = new ProjectHub.Api.Services.ProjectService(ProjectHub.Api.Data.SampleData.CreateProjects());
try
{
    debugService.Create("Mobile app", null);   // duplicate name
}
catch (ProjectHub.Api.Exceptions.BusinessRuleException ex)
{
    Console.WriteLine($"Caught: {ex.Message}");
}
""")
S += H2("7.2 What you saw")
S += TABLE([
    ["Question", "Result"],
    ["Where did Rider stop?", "on `throw new BusinessRuleException($\"A project named '{trimmedName}' already exists.\");` (correct). Exception breakpoints stop when an exception is **thrown**, not when it is caught: the tool for 'where does this error come from?'"],
    ["`trimmedName`?", "`\"Mobile app\"` (correct)"],
    ["After removing try/catch?", "you said 'compile failed'. **Wrong term**, see 7.4"],
], [44, 126])
S += H2("7.3 Reading the Variables panel (your screenshot)")
S += TABLE([
    ["Entry", "What it is"],
    ["`$exception`", "Rider **pseudo-variable**: the exception being thrown; expand for `Message`, `StackTrace`"],
    ["`this = ProjectService`", "the **object whose method is running**; expand to see private fields (`_projects`, `_nextProjectId`)"],
    ["`description`, `name` (icon with parentheses)", "the method's **parameters**: values passed in"],
    ["`trimmedName`, `project`", "**local variables**"],
    ["`project = null`", "not assigned yet: the `throw` happened before `var project = new Project {...}` ran (like `count = 0` in topic 1)"],
], [62, 108])
S += P("**Frames** (next to Variables) would show `Create` at the top and your `Program.cs` line below it, as in topic 2.")
S += H2("7.4 Compile time vs runtime: what really happened")
S += WARN([
    "'Compile failed' means the **build** broke and the program never started. Here the build **succeeded**; the program ran and **crashed at runtime**.",
    "Without `try/catch` the exception is **unhandled**: .NET stops the process and prints `Unhandled exception. ProjectHub.Api.Exceptions.BusinessRuleException: A project named 'Mobile app' already exists.` "
    "The snippet ran before `app.Run()`, so the API never started.",
    "Later, inside an HTTP request, an unhandled exception does **not** kill the server: ASP.NET catches it for that request and returns **500**; topic 12 turns that into proper 404/400 responses.",
], "Correction")

# ---------------------------------------------------------------- PART 8
S += PageBreak()
S += H1("Part 8. Your answers, corrections, interview Q&A")
S += H2("8.1 CHECK round 1: what to improve")
S += TABLE([
    ["Question", "Your answer", "Complete answer"],
    ["Interface vs class + two benefits", "contract vs implementation; interface-typed variable sees only the contract (good). **No benefits given**", "swap implementations (EF in topic 10), fakes in tests, DI (topic 7), decorators"],
    ["How a class matches an interface", "declares it; must have all methods (correct)", "plus: the compiler checks it; interfaces exist at runtime"],
    ["Interface vs abstract class", "contract vs shared helper code (roughly right)", "abstract class can hold state and partial implementation; one base class vs many interfaces"],
    ["`where T : IComparable<T>`", "can call CompareTo; Project -> compile error (correct)", ""],
    ["`throw;` vs `throw ex;`", "correct", ""],
    ["Expected vs unexpected", "NotFoundException as expected (correct); **no unexpected example; skipped where to catch**", "unexpected: duplicate Ids in SingleOrDefault, null name -> NullReferenceException; expected -> 4xx via handler; unexpected -> not caught locally, logged, 500"],
    ["null vs throw", "**mechanics** (SingleOrDefault, `?? throw`)", "design: query (null is a valid answer) vs command that cannot be done"],
    ["Why custom exceptions", "**'reusability'**", "catch by type (expected vs bug), map type -> HTTP status, structured data"],
    ["Why data via constructor", "**did not know**", "no hidden hard-coded dependency, tests choose data, swappable source: constructor injection"],
    ["OrdinalIgnoreCase vs ToLower", "Turkish 'i' (correct)", "also: ToLower allocates new strings; ordinal = raw characters, fast and predictable"],
], [38, 62, 70])
S += H2("8.2 Re-check (all correct)")
S += TABLE([
    ["Question", "Your answer"],
    ["null vs throw", "GetById null is expected ('no project with this id'); AddTask cannot add a task to a non-existing project. Interview wording: query vs command that cannot be carried out."],
    ["Custom exceptions", "catch by type; structured data. Add: so a global handler maps each type to an HTTP status."],
    ["Data via constructor", "no hidden dependency; swappable source; simple dependency injection. Add: tests pass their own data."],
], [40, 130])
S += H2("8.3 Interview questions with model answers")
qa = [
    ("Interface vs class?", "An interface is a contract (members without implementation); a class is an implementation. Code depends on the interface so implementations can be swapped (in-memory -> EF), faked in tests, wired by DI, or decorated."),
    ("How does a C# class 'match' an interface, compared to TS?", "Nominally: it must declare `: IProjectService`, and the compiler checks every member. TS matches by shape; C# interfaces also exist at runtime."),
    ("Interface vs abstract class?", "Interface: contract only, a class can implement many. Abstract class: can have state and partial implementation, only one base class. Interface for contracts/capabilities, abstract class for shared code among closely related types."),
    ("What is polymorphism? Example?", "One interface, many implementations chosen at runtime: `LoggingProjectService` and `ProjectService` both are `IProjectService`; callers do not change."),
    ("What does `where T : IComparable<T>` do?", "Constrains T so CompareTo can be called; types without IComparable<T> (e.g. Project) are rejected at compile time."),
    ("How are C# generics different from TS generics?", "Reified: they exist at runtime (`List<int>` vs `List<string>` are different types, `typeof(T)` works). TS generics are erased."),
    ("`throw;` vs `throw ex;`?", "`throw;` rethrows preserving the original stack trace; `throw ex;` resets it to the current line, losing where the error happened."),
    ("Expected vs unexpected errors?", "Expected: caused by input (duplicate name, missing project) -> custom exceptions -> HTTP 4xx. Unexpected: bugs/infrastructure -> not caught locally -> global handler logs and returns 500."),
    ("When return null and when throw?", "Return null (or use Try pattern) when absence is a normal answer to a query; throw when a command cannot be carried out."),
    ("Why custom exception types?", "Catch by type, map type to HTTP status without parsing messages, carry structured data."),
    ("Why should a service get its dependencies via the constructor?", "Constructor injection: no hidden hard-coded dependencies; tests pass their own data/fakes; implementations are swappable; ASP.NET DI automates it."),
    ("Why `StringComparison.OrdinalIgnoreCase` instead of `ToLower()`?", "No string allocations, no culture dependence (Turkish i), predictable for identifiers."),
    ("What is a constructor? How do you recognize it?", "A member with the class's name and no return type that runs once per `new`; the only place `readonly` fields can be assigned. Primary constructors put parameters on the class line."),
    ("What does `finally` guarantee?", "It runs after success, after a caught exception, and when the exception keeps propagating; used for cleanup (or `using`)."),
    ("Can you put `catch (Exception)` before `catch (NotFoundException)`?", "No: compile error, the later catch would be unreachable. Most specific first."),
    ("What is an exception breakpoint?", "A debugger breakpoint that stops when a given exception type is thrown, even if it is caught later."),
    ("Compile error vs runtime exception?", "Compile error: the build fails, nothing runs. Runtime exception: the program runs and fails while executing; unhandled -> the process (or the request) fails."),
    ("var vs explicit type: when does it matter?", "When you want a different type than the right side: `IProjectService s = new ProjectService(...)` depends on the contract; `var` would be the concrete class."),
]
for q, a in qa:
    S += QA(q, a)

# ---------------------------------------------------------------- PART 9
S += PageBreak()
S += H1("Part 9. Summary")
S += OK([
    "**Interface** = contract, **class** = implementation. C# matches interfaces **nominally** (`: IProjectService`). Program against the interface: swap, test, DI, decorate.",
    "**Abstract class**: state + partial implementation, one base class. **Interfaces**: many per class. Prefer composition over inheritance.",
    "**Generics**: type parameters with **constraints** (`where T : ...`); C# generics are **reified** (exist at runtime).",
    "**Exceptions**: catch by type, most specific first, `when` filters, `finally` always runs. **`throw;`** never `throw ex;`.",
    "**Expected** errors (input) -> custom exceptions -> 4xx. **Unexpected** errors (bugs) -> not caught locally -> logged 500.",
    "**Query returns null, command throws.** Use the Try pattern instead of exceptions for normal 'not found'.",
    "**ProjectService**: constructor injection of data, guard clauses, unique-name business rule with `OrdinalIgnoreCase`, `?? throw`, `nameof`, `AsReadOnly`.",
    "**Constructor**: same name as the class, no return type, runs once per `new`; primary constructors put parameters on the class line.",
    "**Debugging**: .NET exception breakpoints stop at the `throw`; Variables shows `$exception`, `this`, parameters, locals. Unhandled exception = runtime crash, not a compile error.",
], "Key takeaways")
S += H2("Cheat sheet")
S += TABLE([
    ["TS / JS", "C#"],
    ["`interface IFoo { bar(): void }` + `class Foo implements IFoo`", "`public interface IFoo { void Bar(); }` + `public class Foo : IFoo`"],
    ["structural match", "nominal: must declare `: IFoo`"],
    ["`abstract class Base`", "`public abstract class Base`"],
    ["`function f<T extends Comparable<T>>(x: T[])`", "`static T F<T>(IEnumerable<T> x) where T : IComparable<T>`"],
    ["`class MyError extends Error { constructor(m) { super(m) } }`", "`public class MyError(string m) : Exception(m);`"],
    ["`catch (e) { if (e instanceof X) ... }`", "`catch (X ex) { } catch (Exception ex) { }`"],
    ["`throw e` (rethrow)", "`throw;`"],
    ["`constructor(deps) { this.deps = deps }`", "`public Service(IDeps deps) { _deps = deps; }`"],
    ["`x ?? throwError()`", "`x ?? throw new NotFoundException(...)`"],
    ["`a.toLowerCase() === b.toLowerCase()`", "`string.Equals(a, b, StringComparison.OrdinalIgnoreCase)`"],
], [85, 85])
S += H2("Checklist: can you do this without notes?")
S += bullets([
    "Explain interface vs class vs abstract class, with two concrete benefits of interfaces.",
    "Explain why `IProjectService service = new ProjectService(...)` differs from `var service = new ProjectService(...)`.",
    "Read a generic method with a constraint and say what it allows and rejects.",
    "Classify an error as expected or unexpected, with a ProjectHub example, and say where it is handled.",
    "Explain query-returns-null vs command-throws.",
    "Explain `throw;` vs `throw ex;`.",
    "Explain constructor injection and why `ProjectService` receives its data.",
    "Point at the constructor in `ProjectService` and explain each line.",
    "Use a .NET exception breakpoint and read the Variables panel.",
    "Tell a compile error from a runtime exception.",
])
S += H2("What comes next: Topic 4 (async/await)")
S += P("`Task` and `Task<T>` are C#'s `Promise`; `async`/`await` look almost the same as in TS. The differences that matter on a backend: threads and the thread pool, "
       "why I/O must be awaited (scalability), `CancellationToken` (like `AbortController`), and pitfalls (`.Result`, `async void`). "
       "Build: make `ProjectService` async and pass a `CancellationToken` through one path.")

build(OUT, S, "ProjectHub study book | Topic 3: Interfaces, generics, exceptions", "ProjectHub study book: Topic 3, Interfaces, generics, exceptions")
print("ok", OUT)
