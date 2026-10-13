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
