# Lesson 3: Interfaces, generics, exceptions

**Roadmap:** Week 1, Topic 3. **Time:** about 2–3 h.
**Checkpoint:** you can explain *interface vs class*, and you can handle an *expected* error.

**Files for this lesson:**
- `src/ProjectHub.Api/Services/IProjectService.cs`: the contract
- `src/ProjectHub.Api/Services/ProjectService.cs`: the in-memory implementation, with one business rule
- `src/ProjectHub.Api/Exceptions/NotFoundException.cs`, `BusinessRuleException.cs`: our own exception types
- `playground/03-services-exceptions.cs`: runnable demo with 10 sections. Run it from the repo root with `dotnet run --no-cache playground/03-services-exceptions.cs`.

---

## 1. Interfaces

### What an interface is
An interface is a **contract**: a list of members (methods, properties) **without implementation**. A class that implements it promises to provide all of them.
```csharp
public interface IProjectService
{
    Project? GetById(int id);
}

public class ProjectService : IProjectService   // ": IProjectService" = "I implement this contract"
{
    public Project? GetById(int id) => ...;     // must exist, or the build fails
}
```

### The big difference from TypeScript (nominal typing again)
| | TypeScript `interface` | C# `interface` |
|---|---|---|
| How a class "matches" | **structurally**: any object with the right shape fits, no declaration needed | **nominally**: the class must **declare** `: IProjectService` |
| Exists at runtime? | No, erased | Yes: `service is IProjectService` works at runtime |
| Describes data shapes? | Yes, very often (`interface User { name: string }`) | Rarely. Data shapes are classes or records. Interfaces describe **behavior** (methods) |
| Naming | `User`, `ProjectService` | `I` prefix by convention: `IProjectService`, `IEnumerable<T>` |

This matters in practice: in TS you'd write `interface Project { ... }` for data. In C#, data is a class or record (Topic 1), and an interface is a capability or contract, such as "something that can manage projects".

### Why bother: "program against the interface"
Code that **uses** a service should depend on `IProjectService`, not `ProjectService`:
```csharp
IProjectService service = new ProjectService(data);   // the variable's type is the interface
static void PrintProjectCount(IProjectService service) { ... } // works with ANY implementation
```
Benefits, all coming up in this course:
1. **Swap implementations.** Today it's an in-memory list. In Topic 10 it becomes EF Core + SQL Server. Code that only knows `IProjectService` doesn't change.
2. **Testing (Topics 13–14).** A test can pass a fake implementation, so you can test a controller without a database.
3. **Dependency injection (Topic 7).** ASP.NET Core is configured to give `ProjectService` whenever someone asks for `IProjectService`. Controllers never call `new ProjectService(...)` themselves.
4. **Decorators (demo section 7).** `LoggingProjectService` implements the same interface, **wraps** another implementation and adds logging. Callers can't tell the difference.

That's **polymorphism**: one interface, many implementations, chosen at runtime.

### Interface vs class vs abstract class (the interview answer)
| | `interface` | `abstract class` | `class` |
|---|---|---|---|
| Has implementation? | No (except rarely used default methods) | Partly: some members are implemented, some `abstract` | Fully |
| Can have fields / state? | No | Yes | Yes |
| Can you `new` it? | No | No | Yes |
| How many can a class use? | **Many**: `class X : IA, IB, IC` | **One** base class | **One** base class |
| Use for | a contract or capability ("can do X") | shared base code for closely related types | the actual implementation |

Modern .NET code uses interfaces a lot and inheritance little. **Composition over inheritance**: `LoggingProjectService` *contains* another service instead of *inheriting* from one.

---

## 2. Generics

You've been using them since Topic 1: `List<T>`, `Dictionary<TKey, TValue>`, `Func<T, bool>`, `IEnumerable<T>`. A generic is a type or method with a **type parameter** `T` that the caller fills in. It's the same idea as TS generics.

```csharp
// generic METHOD: T is inferred from the argument, like TS
static T Largest<T>(IEnumerable<T> items) where T : IComparable<T> { ... }
Largest(new[] { 3, 9, 4 });                // T = int
Largest(new[] { "pear", "apple" });        // T = string

// generic TYPE
record Page<T>(IReadOnlyList<T> Items, int PageNumber, int TotalCount);
Page<string> names = ...;  Page<TaskItem> tasks = ...;
```

### Constraints: `where T : ...` (TS: `T extends ...`)
Without a constraint, you can only do with `T` what works for *every* type. A constraint lets you use more.
| Constraint | Meaning | Example use |
|---|---|---|
| `where T : IComparable<T>` | T can be compared, so `CompareTo` exists | `Largest<T>` in the demo |
| `where T : class` | T is a reference type | allows `T?` to mean "nullable reference" |
| `where T : struct` | T is a value type | `Nullable<T>` itself is declared like this |
| `where T : new()` | T has a public parameterless constructor | `new T()` inside the method |
| `where T : SomeBaseClass` / `ISomeInterface` | T is or implements it | access its members |
| `where T : notnull` | T is not nullable | dictionary keys |

`Largest(service.GetAll())` **doesn't compile**: `Project` doesn't implement `IComparable<Project>`, so the constraint blocks it at compile time.

### A real difference from TS: C# generics exist at runtime
TS generics are **erased**: at runtime there's only `Array`. C# generics are **reified**: `List<int>` and `List<string>` are different runtime types, `typeof(T)` works inside a generic method, and `List<int>` stores actual `int`s without boxing. You get type safety at runtime, not just at compile time.

---

## 3. Exceptions

### Same core as JS
`try` / `catch` / `finally` and `throw` work like in JS. What C# adds:

| Feature | C# | JS |
|---|---|---|
| Catch by **type** | `catch (NotFoundException ex) { }` then `catch (Exception ex) { }` | one `catch (e)`, then `if (e instanceof ...)` |
| Catch order | most specific **first**. A general catch before a specific one is a **compile error** | n/a |
| Filters | `catch (NotFoundException ex) when (ex.Key is int id && id > 10)` | n/a |
| Rethrow | `throw;` keeps the original stack trace | `throw e` (no `throw;`) |
| What can be thrown | only `Exception` objects (or subclasses) | anything, even strings |

### `throw;` vs `throw ex;` (classic interview question)
Demo section 6 shows it:
```
throw;    -> top frame: ThrowDeepInside()   <- where the error REALLY happened
throw ex; -> top frame: Rethrow(...)        <- original location LOST
```
`throw ex;` **resets the stack trace** to the current line. When you log or debug, you lose where the bug actually was. Always rethrow with `throw;`. The compiler even warns (CA2200). The demo turns that warning off on purpose.

(In the trace, names like `<<Main>$>g__ThrowDeepInside|0_6` are compiler-generated names for local functions in a top-level-statements file. Ignore the decoration and read the method name.)

### Expected vs unexpected errors (the core design idea)
| | Expected error | Unexpected error (bug / infrastructure) |
|---|---|---|
| Examples | duplicate project name, empty title, project id doesn't exist | `NullReferenceException`, database down, `InvalidOperationException` from `First()` |
| Whose fault | the **caller's input** | **our code** or the environment |
| What to do | catch it, tell the user what's wrong (HTTP **4xx**) | don't catch it locally. Let it reach a global handler that logs it and returns HTTP **500** (Topic 12) |
| Our type | `BusinessRuleException`, `NotFoundException` | whatever .NET throws |

Rules of thumb:
- **Catch only what you can handle.** Catching `Exception` everywhere hides bugs. Never write an empty `catch { }` that swallows errors.
- **Don't use exceptions for normal control flow.** If "not found" is an ordinary answer, return `null` or use the **Try pattern** (`dict.TryGetValue`, `int.TryParse`) instead of throwing. Throwing and catching is slow compared to an `if`, and it hides what's normal versus what's exceptional.
- **Custom exception types carry meaning and data.** The global handler in Topic 12 will map `NotFoundException` → 404 and `BusinessRuleException` → 400/409 without inspecting message text. `NotFoundException.EntityName` and `.Key` are data you can log or return.
- `finally` always runs: after success, after a caught exception, and when the exception keeps flying. It's used for cleanup. `using var x = ...;` is the short form for disposing resources (a file, a DB connection) in an automatic `finally`.

### `null` vs exception: what our service does
- `GetById(id)` returns **`Project?`**. "Does project 99 exist?" is a normal **question**, and `null` is a normal answer.
- `AddTask(projectId, ...)` **throws** `NotFoundException`. You asked to *change* a project that doesn't exist, so the **command** can't be done, and the caller must not continue as if it was.

Queries can return "nothing". Commands that can't be carried out throw.

---

## 4. BUILD: what Claude wrote and why

### `Exceptions/NotFoundException.cs` and `BusinessRuleException.cs`
```csharp
public class NotFoundException(string entityName, object key)
    : Exception($"{entityName} with id '{key}' was not found.")
{
    public string EntityName { get; } = entityName;
    public object Key { get; } = key;
}

public class BusinessRuleException(string message) : Exception(message);
```
- **`: Exception(...)`**: inherits from `System.Exception`, the base of all exceptions. That's the one place class inheritance is the norm in everyday code. `: Exception(message)` passes the message to the base class constructor, like `super(message)` in a JS `class MyError extends Error`.
- **Primary constructor** `class NotFoundException(string entityName, object key)`: the parameters are declared on the class line itself (C# 12+). It's short for a constructor that receives them. `EntityName { get; } = entityName` stores one in a read-only property.
- **`object key`**: `object` is the base type of everything (like `unknown` in TS). Ids could be `int` today and `Guid` later, so the exception accepts any key.
- **Why our own types and not `Exception("...")`**: callers and the Topic 12 handler can **catch by type**. Parsing message strings is fragile.
- **Why not the built-in `ValidationException`**: `System.ComponentModel.DataAnnotations.ValidationException` already exists and is used by ASP.NET's model validation. Reusing the name would be confusing, so ours is called `BusinessRuleException`.

### `Services/IProjectService.cs`
- Four members: `GetAll`, `GetById`, `Create`, `AddTask`. This is the **contract** controllers will depend on in Topic 6.
- **Return types are part of the contract:** `IReadOnlyList<Project>` means "you can read it, not change the list", and `Project?` means "may be null, check it".
- Comments document **which exceptions** each method throws. C# has no `throws` clause like Java, so the docs are the contract.

### `Services/ProjectService.cs`
| Line | Why |
|---|---|
| `public class ProjectService : IProjectService` | implements the contract; the compiler checks every member exists |
| **the constructor** `public ProjectService(IEnumerable<Project> initialProjects) { ... }` (same name as the class, no return type; runs once on `new ProjectService(data)`; TS: `constructor(initialProjects: Iterable<Project>) { ... }`) takes the data as a parameter | the service doesn't decide where data comes from. The caller passes it in: `SampleData` today, test data in Topic 13. This is **dependency injection in its simplest form** (Topic 7 automates it) |
| `_projects = initialProjects.ToList()` | its **own copy** (Topic 2: enumerate once; caller's later changes don't affect it) |
| `private readonly List<Project> _projects` | `readonly`: the *field* can't be reassigned after the constructor (the list's *contents* can still change). `_camelCase` = private field naming |
| `.Select(p => p.Id).DefaultIfEmpty(0).Max() + 1` | next id. `DefaultIfEmpty(0)` avoids the **Max-on-empty exception** from Topic 2 when there are no projects |
| `public const int MaxNameLength = 100;` | a compile-time constant; public so the API layer can reuse the same limit later |
| `GetAll() => _projects.AsReadOnly()` | returns a **read-only wrapper**. Casting it back and calling `Add` throws `NotSupportedException` (demo section 8) |
| `GetById(...) => _projects.SingleOrDefault(...)` | `Single`, because an id must be unique: a duplicate would be a bug worth surfacing (Topic 2) |
| `name.Trim()` | `"  Docs portal  "` and `"Docs portal"` must count as the same name |
| the 3 `if ... throw new BusinessRuleException(...)` | **guard clauses**: check and exit early, so the "happy path" below stays flat |
| `string.Equals(a, b, StringComparison.OrdinalIgnoreCase)` | **the business rule**: unique names, case-insensitive. Better than `a.ToLower() == b.ToLower()`, which allocates new strings and depends on the server's **culture** (the famous Turkish "i" problem) |
| `Id = _nextProjectId++` | uses the current value, then increments (post-increment, same as JS) |
| `GetById(projectId) ?? throw new NotFoundException(...)` | **throw expression**: "get it, or throw if null" in one line |
| `nameof(Project)` | the string `"Project"`, checked by the compiler. Rename the class and this follows |

**Known limitations (on purpose, with a note in the code):**
1. **Not thread-safe.** Two requests at the same time could get the same id or corrupt the list. That's fine for a single caller today. When the service is shared across HTTP requests (Topics 6–7), we'll deal with it, and EF Core in Topic 10 makes the database handle ids.
2. **Entities leak.** `GetAll()` is read-only as a *list*, but the `Project` objects inside are mutable. Demo section 8 renames a project from outside the service. Topic 6 fixes this with **DTOs**: the API returns copies (records), never the entities themselves.

### `playground/03-services-exceptions.cs`
| Section | Shows |
|---|---|
| 1 | variable typed as the interface; `GetById` returning `null` |
| 2 | happy path: `Create` (name trimmed), `AddTask` (default status `Todo`) |
| 3 | the business rule rejecting a duplicate (different case), an empty name, a too-long name |
| 4 | `NotFoundException` with data (`EntityName`, `Key`) |
| 5 | multiple `catch` blocks, a `when` filter, `finally` always running |
| 6 | `throw;` vs `throw ex;`: which stack trace survives |
| 7 | polymorphism + decorator: `LoggingProjectService` wraps any `IProjectService`; the calling code is unchanged |
| 8 | read-only list vs mutable entities (the leak) |
| 9 | our own generic method with a constraint |
| 10 | our own generic record `Page<T>`, used for strings and tasks |

---

## 5. DEBUG (locally, in Rider): catch an exception at the moment it's thrown

A caught exception is invisible: the program just continues. Rider can **stop at the `throw` line** anyway.

1. Paste this temporarily into `Program.cs`, right before `app.Run();`:
   ```csharp
   var debugService = new ProjectHub.Api.Services.ProjectService(ProjectHub.Api.Data.SampleData.CreateProjects());
   try
   {
       debugService.Create("Mobile app", null);   // duplicate name
   }
   catch (ProjectHub.Api.Exceptions.BusinessRuleException ex)
   {
       Console.WriteLine($"Caught: {ex.Message}");
   }
   ```
2. **Debug it once with no breakpoints.** It doesn't stop. The exception is caught, and you only see the console line.
3. **Add an exception breakpoint:** menu **Run → Stop on Exception…** → add `BusinessRuleException` → OK. (This is the path in your Rider version. Other versions call it "View Breakpoints → + → .NET Exception Breakpoint"; if neither matches, use Help → Find Action and type "exception".)
4. **Debug again.** Rider now stops **inside `ProjectService.Create`, on the `throw` line**, even though the exception will be caught.
5. Inspect:
   - **Variables:** `trimmedName`, and expand `_projects` (and `this`).
   - **Frames:** the top is `Create`. Below it, find *your* line in `Program.cs`.
6. **Break it:** remove the `try/catch` (keep only the `Create` call) and debug again. Now the exception is **unhandled**. What does Rider show, and what happens to the app?
7. Clean up: delete the snippet and remove the exception breakpoint in the same dialog.

---

## 6. CHECK: answer these in your own words

1. Interface vs class: what's the difference, and why does `ProjectService` implement `IProjectService`? Give two concrete benefits.
2. A TS interface is matched by shape. How does a C# class "match" an interface?
3. Interface vs abstract class: when would you use each?
4. What does `where T : IComparable<T>` allow you to do inside `Largest<T>`? What happens if you call it with `Project`?
5. `throw;` vs `throw ex;`: what's the difference?
6. Expected vs unexpected error: give one example of each from ProjectHub. Which do you catch, and where?
7. Why does `GetById` return `null` but `AddTask` throws `NotFoundException`?
8. Why create custom exception types instead of `throw new Exception("not found")`?
9. Why does `ProjectService` take its data in the constructor instead of calling `SampleData.CreateProjects()` itself?
10. Why `StringComparison.OrdinalIgnoreCase` instead of `ToLower()`?
