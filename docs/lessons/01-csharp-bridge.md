# Lesson 1: Setup + the C# bridge (types, nullability, classes, records)

**Roadmap:** Week 1, Topic 1. **Time:** about 2–3 h.
**Checkpoint:** you can run the solution, and you can explain *class vs record* and *nullable warnings*.

---

## 0. Setup on your Mac (do this once, about 30 min)

1. **.NET 10 SDK:** https://dotnet.microsoft.com/download/dotnet/10.0, then check with `dotnet --list-sdks`.
2. **Editor** (pick one):
   - **JetBrains Rider:** free for non-commercial use. It's the closest thing to Visual Studio and has the best debugger on macOS.
   - **VS Code + "C# Dev Kit" extension:** lighter. Also works.
3. **Docker Desktop:** then run `docker compose up -d` in the repo root to start SQL Server. We need it from Topic 8.
4. **DB tool** (SSMS is Windows-only): the VS Code **"SQL Server (mssql)"** extension (it shows execution plans), or DBeaver.
5. Clone the repo, check out the branch, then:
   ```bash
   dotnet build
   dotnet run --project src/ProjectHub.Api
   # open http://localhost:<port>/weatherforecast  (port is printed in the console)
   ```

### What the scaffold contains (read it, it's short)
| File | What it is | TS/Node analogy |
|---|---|---|
| `ProjectHub.slnx` | Solution: a list of projects | monorepo root / workspaces |
| `src/ProjectHub.Api/ProjectHub.Api.csproj` | Project file: target framework, NuGet packages | `package.json` + `tsconfig.json` |
| `Program.cs` | App startup: registers services, builds the HTTP pipeline | `server.ts` with Express setup |
| `Controllers/WeatherForecastController.cs` | Template example endpoint (we delete it in Topic 6) | Express router |
| `appsettings*.json` | Configuration | `.env` / config files |
| `Properties/launchSettings.json` | How `dotnet run` starts the app locally (ports, env) | `scripts` in `package.json` |

Look at the csproj: `<Nullable>enable</Nullable>` is roughly C#'s `strictNullChecks`. It matters a lot for this lesson.

---

## 1. Types: what's different from TypeScript

### Nominal vs structural typing: the biggest mindset change
In TypeScript, two types with the same shape are compatible (**structural** typing).
In C#, a type is compatible only if it **is** that type, or inherits from or implements it (**nominal** typing).
```csharp
class A { public string Name { get; set; } = ""; }
class B { public string Name { get; set; } = ""; }
A a = new B(); // ❌ compile error. Same shape doesn't matter.
```

### Numbers: TS has one, C# has several
| C# | Use for |
|---|---|
| `int` | ids, counts (32-bit) |
| `long` | big ids/counts |
| `decimal` | **money**: exact decimal math |
| `double` | measurements, math (floating point, like JS `number`) |
| `bool`, `string`, `char` | as expected (`char` is a single character, `'a'`) |
| `DateTime` / `DateTimeOffset` | dates. Store UTC (`DateTime.UtcNow`). |
| `Guid` | UUIDs |

`var x = 5;` is **type inference**, like `const x = 5`. `x` is still a strongly typed `int` forever. `var` is *not* JS `var`.

### Value types vs reference types
- **Value types** (`int`, `bool`, `decimal`, `DateTime`, `Guid`, `enum`, `struct`): the variable holds the value itself, and assignment copies it. They can't be `null` unless you write `int?`.
- **Reference types** (`class`, `record`, `string`, arrays, `List<T>`): the variable holds a reference, like JS objects. Assignment copies the reference.
- `string` is a reference type, but it's immutable, and `==` compares content. So it *feels* like a JS string.

### No `undefined`
Every variable or field has a **default** value: `0`, `false`, or `null` for references. There's no "missing property", because the compiler knows every property of a type.

### Enums
```csharp
public enum TaskItemStatus { Todo, InProgress, Done } // stored as int 0,1,2 by default
var s = TaskItemStatus.Done;
```
This is like a TS `enum`. A union of string literals (`'todo' | 'done'`) has no direct equivalent, and enums are what C# uses instead.

---

## 2. Nullability

With `<Nullable>enable</Nullable>`:
```csharp
string name = null;      // ⚠️ warning CS8600: you said it can't be null
string? description = null; // ✅ the '?' means "may be null"

int count = null;        // ❌ error: value types are never null...
int? maybeCount = null;  // ✅ ...unless you write int?  (that's Nullable<int>, has .HasValue/.Value)
```

The same operators as TS:
```csharp
int len = description?.Length ?? 0;   // ?. and ??
description ??= "none";                // ??=
if (description is null) { }           // preferred null check
if (description is not null) { }
string sure = description!;            // '!' = "trust me": same as TS non-null assertion, avoid it
```

**Important difference:** for reference types, nullability is **compile-time warnings only**. At runtime, `string` can still hold `null`, for example from JSON or a database, and you get a `NullReferenceException`, the C# version of "Cannot read properties of undefined". Treat nullable warnings as bugs and don't ignore them.

Warnings you'll meet constantly:
- **CS8618:** "Non-nullable property 'Name' must contain a non-null value when exiting constructor." You declared `string Name` but nothing guarantees it gets set. Fixes: make it `required`, set it in a constructor, give it a default, or make it `string?` if null is genuinely valid.
- **CS8602:** "Dereference of a possibly null reference." You used `x.Something` where `x` may be null.

---

## 3. Classes

```csharp
public class Project
{
    public int Id { get; set; }                      // property: get/set accessors
    public required string Name { get; set; }        // 'required': must be set when creating the object
    public string? Description { get; set; }         // optional
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow; // 'init': settable only during creation
    public List<TaskItem> Tasks { get; set; } = [];  // collection expression (like `= []`)
}

var p = new Project { Name = "Website" };  // object initializer: like `{ name: "Website" }`
p.Name = "Website v2";                     // fine: it has set
// p.CreatedAt = DateTime.UtcNow;          // ❌ init-only
// var bad = new Project { };              // ❌ error: required member 'Name' not set
```

- A **property** (`{ get; set; }`) is not a plain field. It's a pair of accessor methods. Public data in C# is always properties. Fields (`private int _count;`) are private internals.
- Access modifiers: `public`, `private` (the default for members), `protected`, `internal` (visible within the project).
- A class can also have a constructor and methods (behavior). We'll add those in Topic 3.

---

## 4. Records

```csharp
public record ProjectSummary(int Id, string Name, int TaskCount); // "positional record": one line
```
This one line generates a constructor, `init`-only properties, **value equality**, a readable `ToString()`, and deconstruction.

```csharp
var a = new ProjectSummary(1, "Web", 3);
var b = new ProjectSummary(1, "Web", 3);
a == b;                            // True: compared by VALUES

var c = a with { TaskCount = 4 };  // non-destructive copy, like `{ ...a, taskCount: 4 }`
Console.WriteLine(c);              // ProjectSummary { Id = 1, Name = Web, TaskCount = 4 }
```
Two instances of a **class** with identical data are `==` only if they're the *same object* (reference equality, like `===` on JS objects).

### Class vs record: the interview answer
| | `class` | `record` |
|---|---|---|
| Equality | reference (same object?) | value (same data?) |
| Mutability | usually mutable | usually immutable (`init`), changed with `with` |
| Meaning | a thing with **identity** that changes over time | a **value** or data snapshot |
| In a .NET backend | **entities** (EF Core tracks and changes them) | **DTOs** (request/response contracts), messages, results |

Rule of thumb: an entity with an `Id` that gets updated is a class. Data moving across a boundary (HTTP in/out) is a record.

(`struct` / `record struct` also exist. They're value types for small values. You'll rarely write them in backend code, but know they exist.)

---

## 5. BUILD: your exercise

Create `src/ProjectHub.Api/Entities/` with two files. **You write them.**

**`Project.cs`**
- `Id` (int), `Name` (required, non-null), `Description` (optional), `CreatedAt` (set once, defaults to UTC now), `Tasks` (a list of `TaskItem`, never null)

**`TaskItem.cs`**
- `Id`, `ProjectId` (int), `Title` (required), `Status` (an enum `TaskItemStatus`: Todo / InProgress / Done, default Todo), `CreatedAt`
- Why `TaskItem` and not `Task`? Think about it. Hint: Topic 4.

Conventions to follow:
- Put the namespace at the top: `namespace ProjectHub.Api.Entities;` (file-scoped, the modern style)
- PascalCase for types, properties and methods. camelCase for locals and parameters. `_camelCase` for private fields.
- One public type per file, with the file named after the type.

Then make sure `dotnet build` shows **0 warnings** for your files.

### Experiment (do it in a scratch file, don't commit it)
.NET 10 can run a single `.cs` file with no project: `dotnet run playground.cs`. Try:
1. Two identical `class` instances: `==`? Then two identical `record` instances: `==`?
2. `with` on a record, then print both. Did the original change?
3. Remove `required` from `Name` and build. Read the warning. Then try `string? Name` and see what changes for code that *uses* `Name.Length`.
4. `int? x = null; Console.WriteLine(x.HasValue);`, then `x.Value`. What happens at runtime?

## 6. DEBUG (locally, in Rider or VS Code)
In `Program.cs`, temporarily create a `Project` with two `TaskItem`s right before `app.Run()`. Put a **breakpoint** there, run with the debugger (F5), and inspect the object in **Locals**. Expand `Tasks`. Then remove the temporary code.

## 7. CHECK: answer these in your own words (I'll quiz you)
1. Class vs record: when do you use each in a backend, and why?
2. What does `string?` actually change: compile time, runtime, or both?
3. What's the difference between `string?` and `int?`?
4. What does CS8618 mean and what are the ways to fix it?
5. What does `required` do? And `init`?
6. Why is `A a = new B();` an error even though the shapes match?
7. Which numeric type do you use for money, and why not `double`?

When you're done: push your code (or paste it into the chat) and say "review topic 1".
