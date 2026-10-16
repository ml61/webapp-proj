# Interview question bank

Questions grow topic by topic. Answer out loud, without notes. ✅ a question once you can answer it confidently.
At the end of the program Claude runs a mock interview from this list.

## Topic 1: C# bridge
- [ ] Class vs record: differences, and when to use each in a backend
- [ ] Value type vs reference type, with examples
- [ ] What do nullable reference types (`string?`) do at compile time vs runtime?
- [ ] `string?` vs `int?`: what's different under the hood?
- [ ] CS8618: what does it mean and how do you fix it?
- [ ] `required` vs `init` vs a constructor parameter
- [ ] Structural (TS) vs nominal (C#) typing
- [ ] `decimal` vs `double`: which one for money, and why
- [ ] What does `with` do on a record?
- [ ] What is a property, and how is it different from a field?
- [ ] `DateTime.UtcNow` vs `DateTime.Now`: what is stored, and which one for `CreatedAt`?
- [ ] Why is an EF Core entity a class and not a record? What is "identity" for an entity?
- [ ] Why `TaskItem` and not `Task`?
- [ ] Debugger: a breakpoint is hit on a line. Has that line run yet?

## Topic 2: Collections + LINQ
- [ ] Translate map / filter / find / some / every / flatMap / reduce into LINQ
- [ ] `First` vs `FirstOrDefault` vs `Single` vs `SingleOrDefault`: when to use each
- [ ] What does `FirstOrDefault` return for a `List<int>` when nothing matches?
- [ ] What is deferred execution? Name two consequences
- [ ] When and why do you call `ToList()`? What is the danger of calling it too early with EF Core?
- [ ] `List<T>` or `IEnumerable<T>` as a method parameter, and why
- [ ] `Dictionary` vs `List` for lookups by id (Big-O)
- [ ] `list.Sort()` vs `OrderBy`
- [ ] What is an extension method? How does `.Where` become available on a `List<T>`?
- [ ] `IEnumerable<T>` vs `IQueryable<T>`: where does the filter run?
- [ ] `Func<T, bool>` and `Action<T>`: what are they?
- [ ] What does `var` do? When is it required? Is it dynamic typing?
- [ ] Which LINQ calls throw where JS would return undefined? (First, Single, Max on empty, dict[missing], ToDictionary duplicates)
- [ ] Debugger: what does the call stack (Frames) show, and how do you use it?

## Topic 3: Interfaces, generics, exceptions
- [ ] Interface vs class: what is the difference? Two concrete benefits of programming against an interface
- [ ] How does a C# class "match" an interface, compared to TypeScript?
- [ ] Interface vs abstract class: when do you use each?
- [ ] What is polymorphism? Give an example (decorator)
- [ ] What does a generic constraint like `where T : IComparable<T>` do? What happens with a type that doesn't satisfy it?
- [ ] How are C# generics different from TS generics (reified vs erased)?
- [ ] `throw;` vs `throw ex;`
- [ ] Expected vs unexpected errors: examples, which do you catch, and where?
- [ ] When do you return null and when do you throw? (query vs command)
- [ ] Why custom exception types?
- [ ] Why should a service receive its dependencies through the constructor?
- [ ] What is a constructor, and how do you recognize it? Classic vs primary constructor
- [ ] `StringComparison.OrdinalIgnoreCase` vs `ToLower()`
- [ ] Compile error vs runtime exception; what happens to an unhandled exception?
- [ ] `var` vs an explicit interface type: when does it change the meaning?
- [ ] Debugger: what is an exception breakpoint?

## Topic 4: Async/await
- [ ] `Task<T>` vs `Promise<T>`: what is the same, what is different (thread pool vs one thread)?
- [ ] Why should backend I/O be awaited? (thread, pool, starvation)
- [ ] Does async make a request faster? What does it improve? Where does it not help?
- [ ] What is thread-pool starvation?
- [ ] What is a `CancellationToken`? Who creates it, who passes it, where does ASP.NET get one?
- [ ] Why is `.Result` / `.Wait()` bad?
- [ ] What is wrong with `async void`? With calling an async method without `await`?
- [ ] Where does an exception thrown in an async method surface?
- [ ] `Task.WhenAll` vs sequential awaits; result order; why not with one EF `DbContext`?
- [ ] What is a race condition? What is check-then-act, and how do you fix it?
- [ ] Why can't you `await` inside a `lock`?
- [ ] Is `List<T>` thread-safe? What can happen without a lock?
- [ ] What does a lock guarantee about which thread wins?
- [ ] Why make `IProjectService` async when the data is in memory?

## Topic 5: Debugging
- [ ] How do you debug a bug locally? (reproduce, locate, hypothesize, verify, fix, re-run)
- [ ] Why use a debugger instead of `Console.WriteLine`? When are logs the right tool?
- [ ] Step Over vs Step Into vs Step Out vs Run to Cursor
- [ ] What is a conditional breakpoint? A hit count? A logpoint?
- [ ] What does an exception breakpoint give you that a console stack trace doesn't?
- [ ] Watch vs Evaluate Expression
- [ ] How do you find out which caller passed a bad value? (Frames)
- [ ] What is `2 / 4` in C#, and why? What does `Math.Round(2.5)` return?
- [ ] How can `Split(' ')` crash? Why read imported data defensively?
- [ ] How did a "read-only" report delete data? (copied reference)
- [ ] The code looks fixed but the old behaviour remains: what do you suspect first?

## Topic 6: HTTP + REST, controllers, DTOs
- [ ] What do 200, 201, 204, 400, 404, 409, 500 mean? A ProjectHub example of each
- [ ] 400 vs 409
- [ ] What is idempotency? Which verbs are idempotent, and why does it matter for retries?
- [ ] What does `CreatedAtAction` return? What is the `Location` header for?
- [ ] Why DTOs instead of returning entities? (five reasons)
- [ ] What does `[ApiController]` do?
- [ ] `ActionResult<T>` vs `IActionResult`
- [ ] Where does an action's `CancellationToken` come from?
- [ ] Why is the in-memory `ProjectService` a singleton, and why does that need a lock?
- [ ] Why does `/api/projects/abc` return 404 with an empty body?
- [ ] What is ProblemDetails?
- [ ] How does an exception thrown in the service become an HTTP status code?
- [ ] Why must `catch (ConflictException)` come before `catch (BusinessRuleException)`?
- [ ] What does `: ControllerBase` give a controller? Why can you call `Ok()` without `this.`?
- [ ] Why return enums as strings in JSON?

## Topic 7: DI, middleware, configuration, ILogger
- [ ] What is dependency injection, and what are two benefits?
- [ ] What is the DI container, and how does it build a controller with nested dependencies?
- [ ] Singleton vs Scoped vs Transient (with an example of each)
- [ ] Which lifetime for a `DbContext`? For an in-memory store?
- [ ] What is a captive dependency? What does ASP.NET do about it?
- [ ] Which classes get constructor injection? What happens if you `new` a class yourself?
- [ ] Composition vs inheritance
- [ ] What is middleware? Why does the order matter? How is it like Express?
- [ ] Why set a response header in `OnStarting`?
- [ ] How does ASP.NET find controllers? (`AddControllers` / `MapControllers`)
- [ ] Configuration sources and precedence; overriding with an environment variable
- [ ] What are the Options pattern and `ValidateOnStart` for?
- [ ] Why message templates instead of string interpolation in log calls?
- [ ] What does the `T` in `ILogger<T>` do? How do log levels work?
