# Lesson 2: Collections + LINQ

**Roadmap:** Week 1, Topic 2. **Time:** about 2–3 h.
**Checkpoint:** you can translate `map` / `filter` / `find` (and friends) into LINQ, and explain deferred execution.

**Files for this lesson:**
- `src/ProjectHub.Api/Data/SampleData.cs`: sample projects and tasks (also reused in Topic 6)
- `playground/02-linq.cs`: runnable demo with 13 sections. Run it from the repo root with `dotnet run --no-cache playground/02-linq.cs`.

---

## 1. Collections: what replaces the JS array and Map

| C# | What it is | TS / JS analogy |
|---|---|---|
| `T[]` (array) | fixed size, fast index access | `T[]` you never push to |
| `List<T>` | growable list: `Add`, `Remove`, `Count`, `[i]` | `Array<T>` (the everyday collection) |
| `Dictionary<TKey, TValue>` | key → value lookup in O(1) | `Map<K, V>` |
| `HashSet<T>` | unique values, fast `Contains` | `Set<T>` |
| `IEnumerable<T>` | "something you can loop over". Read-only, lazy | `Iterable<T>` |
| `IReadOnlyList<T>` / `IReadOnlyCollection<T>` | read-only view with `Count` (and index) | `ReadonlyArray<T>` |

Differences from JS worth knowing:
- `List<T>` has **`Count`**, not `length`. Arrays have `Length`. (Yes, it's inconsistent.)
- `List<T>` only holds `T`. You can't push a string into `List<int>`, because generics are checked at compile time **and** at runtime.
- `dict[key]` **throws** `KeyNotFoundException` when the key is missing. JS `map.get(key)` returns `undefined`. In C#, use `TryGetValue` when a key may be missing.
- `list.Sort()` sorts **in place** (like JS `sort`). LINQ `OrderBy` returns a **new** sequence and leaves the source untouched (like `toSorted`).

### Interfaces as parameter and return types
`IEnumerable<T>` is an **interface** (Topic 3 covers interfaces properly). `List<T>`, arrays, `HashSet<T>` and others all implement it. That's why a method taking `IEnumerable<T>` accepts any of them, much like a TS function taking `Iterable<T>`.
Typical rule: **accept the most general type you need, return the most specific useful type.** For example, a parameter is `IEnumerable<TaskItem>`, and a result is `List<TaskItem>` or `IReadOnlyList<TaskItem>`.

---

## 2. Lambdas and delegates

The lambda syntax is the same as TS arrow functions:
```csharp
t => t.Status == TaskItemStatus.Done          // one parameter, expression body
(a, b) => a + b                                // two parameters
t => { Console.WriteLine(t.Title); return t.Id; } // block body
```
A lambda needs a **delegate type** to live in. Delegate types are the C# version of function types:

| C# | TS | Meaning |
|---|---|---|
| `Func<TaskItem, bool>` | `(t: TaskItem) => boolean` | takes `TaskItem`, returns `bool` (a predicate) |
| `Func<int, int, int>` | `(a: number, b: number) => number` | the **last** type argument is the return type |
| `Action<string>` | `(s: string) => void` | returns nothing |

`Where` is declared roughly as `Where<T>(this IEnumerable<T> source, Func<T, bool> predicate)`. That's why you can pass `t => t.Status == ...` to it.

---

## 3. What LINQ actually is

**LINQ (Language Integrated Query)** is a set of **extension methods** on `IEnumerable<T>` in the `System.Linq` namespace. It's imported automatically in .NET projects (implicit usings).
- An **extension method** is a static method that *looks* like an instance method. `tasks.Where(...)` is really `Enumerable.Where(tasks, ...)`. That's how a `List<T>` "gets" `.Where` without `List<T>` defining it. TS has no direct equivalent. Imagine adding methods to `Array.prototype`, but in a type-safe and scoped way, without changing the original class.
- Each operator returns a new `IEnumerable<T>`, so they **chain**, like `.filter().map()`.

### The translation table (the checkpoint)

| JS / TS | LINQ | Note |
|---|---|---|
| `filter(fn)` | `Where(fn)` | |
| `map(fn)` | `Select(fn)` | |
| `flatMap(fn)` | `SelectMany(fn)` | |
| `find(fn)` | `FirstOrDefault(fn)` | returns `null` (or `default`) when not found |
| `findIndex(fn)` | `List<T>.FindIndex(fn)` | a List method, not LINQ |
| `some(fn)` | `Any(fn)` | `Any()` with no args = "is not empty" |
| `every(fn)` | `All(fn)` | **true on an empty sequence** |
| `includes(x)` | `Contains(x)` | |
| `filter(fn).length` | `Count(fn)` | |
| `reduce(fn, seed)` | `Aggregate(seed, fn)` | prefer `Sum`, `Max`, `Min`, `Average` when they fit |
| `toSorted((a,b)=>...)` | `OrderBy(key)` / `OrderByDescending(key)` + `ThenBy(key)` | you give a **key**, not a comparator |
| `slice(start, end)` | `Skip(n).Take(m)` | paging |
| `[...new Set(xs)]` | `Distinct()` | |
| `Object.groupBy(xs, fn)` | `GroupBy(fn)` | each group has `.Key` and is itself a sequence |
| `new Map(xs.map(x => [k, v]))` | `ToDictionary(x => k, x => v)` | **throws** on duplicate keys |
| `Math.max(...xs.map(fn))` | `Max(fn)` | **throws** on an empty sequence of value types |
| item with max value | `MaxBy(fn)` / `MinBy(fn)` | returns the whole item |
| `Array.from(iter)` | `ToList()` / `ToArray()` | runs the query and stores the result |

### The "find" family: pick by intent

| Method | 0 matches | 1 match | 2+ matches | Use when |
|---|---|---|---|---|
| `First` | throws | item | first one | it **must** exist; not existing is a bug |
| `FirstOrDefault` | `null` / default | item | first one | it may not exist (like `find`) |
| `Single` | throws | item | **throws** | exactly one must exist (lookup by unique key) |
| `SingleOrDefault` | `null` / default | item | **throws** | zero or one; more is a data bug |

`Single` asserts that your data is correct. If two tasks share an Id, you want a loud error, not a silently picked first one.

### Method syntax vs query syntax
```csharp
allTasks.Where(t => t.Status != TaskItemStatus.Done).OrderBy(t => t.Title).Select(t => t.Title); // method syntax
from t in allTasks where t.Status != TaskItemStatus.Done orderby t.Title select t.Title;          // query syntax
```
They compile to the **same thing**. Method syntax is what most teams use. Recognize query syntax when you see it, because it looks like SQL.

### Anonymous types
`Select(t => new { t.Id, Upper = t.Title.ToUpper() })` creates an object of a compiler-generated type with read-only properties. It's like returning an object literal from `map`. You can only use it with `var` inside the method. To return it from a method or an API, define a **record** instead (section 8 of the demo: `ProjectSummary`).

---

## 4. Deferred execution: the most important idea in this lesson

```csharp
IEnumerable<int> query = source.Where(n => n > 1); // NOTHING runs here: this is a recipe
foreach (var n in query) { }                         // runs NOW
foreach (var n in query) { }                         // runs AGAIN, from scratch
var list = query.ToList();                           // runs once and stores the result
```
- Operators that return `IEnumerable<T>` (`Where`, `Select`, `OrderBy`, `Skip`, `Take`, `GroupBy`, ...) are **deferred**: they describe work.
- The work happens when something **enumerates** the sequence: `foreach`, `ToList` / `ToArray` / `ToDictionary`, `Count()`, `First()`, `Any()`, `Sum()`, `string.Join`, and so on.
- JS analogy: a **generator function**. Calling it does nothing, and iterating it runs the body. JS array methods are *eager* by contrast: `filter` immediately builds a new array.

Consequences (demo section 11):
1. **The query sees later changes to the source.** It ran after `source.Add(4)`, so the 4 was included.
2. **Multiple enumeration repeats the work.** Two loops means the filter runs twice. With a database query (EF Core), that means **two SQL round-trips**. Rider even warns: "Possible multiple enumeration".
3. **`ToList()` freezes a snapshot.** Call it when you need the result more than once, or when you want to stop the query from seeing later changes.

### Preview: `IEnumerable<T>` vs `IQueryable<T>` (Topic 10–11)
With EF Core, `db.Tasks.Where(t => t.Status == Done)` is an `IQueryable<T>`. The lambda is **not** executed in C#. EF reads it as an *expression tree* and translates it into SQL (`WHERE Status = 2`). Same LINQ syntax, completely different execution:
- `IEnumerable<T>`: LINQ to Objects. Runs in memory, in C#.
- `IQueryable<T>`: LINQ to Entities. Translated to SQL and runs in the database.

The classic bug: call `ToList()` too early, and you load the whole table into memory, then filter in C#. We'll look at the generated SQL in Topic 11.

---

## 5. Gotchas (the demo shows each one)

| Gotcha | What happens | Fix |
|---|---|---|
| `First(...)` with no match | `InvalidOperationException` | `FirstOrDefault` + null check, if "not found" is valid |
| `Single(...)` with 2+ matches | `InvalidOperationException` | use `Single` only for unique keys |
| `Max()` / `Min()` / `Average()` on an empty sequence of value types | `InvalidOperationException` | check `Any()` first, or project to a nullable: `Max(t => (DateTime?)t.CreatedAt)` returns `null` |
| `All(...)` on an empty sequence | returns `true` | decide whether "empty" should count as success |
| `dict[missingKey]` | `KeyNotFoundException` | `TryGetValue(key, out var value)` |
| `ToDictionary` with duplicate keys | `ArgumentException` | make sure keys are unique, or use `GroupBy` / `ToLookup` |
| Multiple enumeration | work (or SQL) runs again | `ToList()` once and reuse |
| Changing a `List` inside its own `foreach` | `InvalidOperationException: Collection was modified` | iterate over a copy (`ToList()`), or collect the changes and apply them after the loop |

---

## 6. BUILD: what Claude wrote and why

### `src/ProjectHub.Api/Data/SampleData.cs`
- **`public static class SampleData`**: a static class can't be instantiated and holds only static members. It's like a TS module exporting functions. It's a good fit for "a bag of helper data".
- **`CreateProjects()` returns a new list on every call**, instead of storing one static list. A shared static list would be **global mutable state**: one caller's `Add` would show up for everyone, and in a web server, for every request and thread at once. A factory method gives every caller its own copy.
- **Fixed dates with `DateTimeKind.Utc`**: the output is deterministic (the same every run). `DateTimeKind.Utc` marks the value as UTC, consistent with `UtcNow` from Topic 1.
- **Collection expressions `[ ... ]`** build the `List<Project>` and each `Tasks` list. The target type (`List<Project>`) tells the compiler which collection to create.
- **`init` on `CreatedAt` still allows setting it here**, because this is an object initializer: the moment of creation.
- `Status` is omitted for some tasks on purpose. They get the default `Todo` from the entity's initializer.
- Project 3 has **no tasks** on purpose. Empty collections are where the `All`, `Max` and `Average` gotchas appear.
- **Where it lives:** `Data/` in the API project. Topic 6 uses it to fill the in-memory storage behind the first real endpoints.

### `playground/02-linq.cs`
- **`#:project ../src/ProjectHub.Api/ProjectHub.Api.csproj`**: a .NET 10 file-based app directive. It references our API project, so the demo uses the real `Project`, `TaskItem` and `SampleData`. It's like importing from a workspace package.
- **`record ProjectSummary(...)`** at the bottom: a DTO-shaped result (Topic 1: records for data that crosses a boundary). Section 8 shows a real projection pattern: entity → summary DTO. You'll see it again in Topics 6 and 11.
- **Named arguments** `TaskCount: p.Tasks.Count`: optional labels at the call site, for readability. They don't change behavior.
- **`static void Section(...)` / `static void Try(...)`**: local helper functions. `static` means they can't capture variables from the surrounding code, which keeps them simple and side-effect free.
- **`Func<string>` in `Try`**: the parameter is a function that returns a string (TS: `() => string`). That's how a piece of code is passed in to be run inside `try/catch`.
- **`foreach (var (status, count) in countByStatus)`**: **deconstruction** of each `KeyValuePair` into two variables. It's like `for (const [status, count] of map)`.
- **`$"{t.Status,-10} {t.CreatedAt:yyyy-MM-dd}"`**: interpolated strings with **alignment** (`,-10` = pad to 10 characters, left-aligned) and **format** (`:yyyy-MM-dd`). It's like template literals, with formatting built in.

---

## 7. DEBUG (locally, in Rider): see deferred execution with your own eyes

1. Open `playground/02-linq.cs` in Rider. If Rider can't run or debug the file directly, use the fallback in step 5.
2. In section 11, put a breakpoint **inside the lambda**, on `evaluations++`. Click the gutter on that line. If Rider asks, choose to break on the lambda rather than the whole line.
3. Debug the file. Watch **when** the breakpoint is hit. It's not on the line that defines `query`. It's during `string.Join(...)` (the first enumeration), then again for the second.
4. Each time it stops, open the **Frames / Call Stack** panel. You'll see `Where` iterator code being called from `string.Join`. That's the evidence: the filter runs when something reads the sequence. Add `evaluations` to **Watch** and see it increase.
5. **Fallback:** temporarily paste section 11 into `Program.cs` before `app.Run();` (like in Topic 1), debug the API, then delete it.

**Break it once:** in section 10, add a second project with `Id = 2` to the list before `ToDictionary` and run it. Read the exception (`ArgumentException: An item with the same key has already been added`). Then undo the change.

---

## 8. CHECK: answer these in your own words

1. Translate: `tasks.filter(t => t.status === 'Done').map(t => t.title)`. Then `tasks.find(t => t.id === 3)`. Then `tasks.some(...)` and `tasks.every(...)`.
2. `First` vs `FirstOrDefault` vs `Single`: when do you use each?
3. What is deferred execution? Name two consequences.
4. When and why do you call `ToList()`?
5. `List<T>` vs `IEnumerable<T>`: which one for a parameter, and why?
6. `Dictionary` vs `List` for looking up a project by id: why?
7. What's the difference between `list.Sort()` and `OrderBy`?
8. What is an extension method, and how does it make `.Where` available on a `List<T>`?
9. (Preview) `IEnumerable<T>` vs `IQueryable<T>`: where does the filter run?
