# Lesson 5: Debugging fundamentals (Debug Lab A)

**Roadmap:** Week 1, Topic 5. **Time:** about 2–3 h. **Where:** locally, in Rider (the cloud session has no visual debugger).
**Checkpoint:** you find a bug **without `Console.WriteLine`**, and you can explain how you found it.

**Files for this lesson:**
- `src/ProjectHub.Api/Labs/DashboardReport.cs`: **contains 3 planted bugs.** Don't read it looking for them; find them with the debugger.
- `src/ProjectHub.Api/Labs/DebugLabA.cs`: the runner that reproduces the three bug reports (not buggy)
- `playground/05-debug-lab.cs`: runs the lab without the debugger, to see the symptoms. Run it from the repo root with `dotnet run playground/05-debug-lab.cs`.

---

## 1. Why a debugger instead of `Console.WriteLine`

| `Console.WriteLine` / `console.log` debugging | Debugger |
|---|---|
| you must guess **in advance** what to print | you see **every** variable at the paused moment, including ones you didn't think of |
| change code → rebuild → rerun for every new question | ask new questions **while paused**: Watches, Evaluate Expression |
| shows values, not **how you got here** | the **call stack** shows the whole chain of calls |
| prints for every loop iteration (noise) | **conditional breakpoints** stop only on the interesting iteration |
| leftover prints get committed | nothing to clean up in the code |

In the interview, "how do you debug?" isn't answered by "I add logs". Logs are for **production**, where you can't attach a debugger (Topic 17). Locally, you use the debugger.

## 2. The method (more important than any tool)

1. **Reproduce.** Make the bug happen reliably. Our runner does this for you: each bug report has a visible symptom.
2. **Locate.** Find *where* the wrong value first appears. Start where the symptom shows, and walk backwards (call stack, Step Into) until the data is correct on one line and wrong on the next.
3. **Hypothesize.** Say *why* it's wrong, in one sentence: "this divides two ints, so…".
4. **Verify the hypothesis in the debugger** before you change code. Evaluate the corrected expression while paused and check you get the right value.
5. **Fix**, then **re-run the reproduction**. The symptom must be gone, and nothing else may break. Later (Topic 13) this becomes a **unit test** that guards against the bug coming back.

## 3. The Rider toolbox

| Tool | What it does | Use it when | Where in Rider |
|---|---|---|---|
| **Breakpoint** | pauses **before** a line runs (Topic 1) | you know roughly where to look | click the gutter |
| **Step Over** | runs the current line, stops at the next one in the same method | the line's internals don't interest you | Debug toolbar, or Run → Debugging Actions |
| **Step Into** | enters the method called on the current line | the bug might be inside that call | Debug toolbar |
| **Smart Step Into** | lets you pick **which** call to enter when a line has several (e.g. `result.Add(new X(..., Calc(a, b)))`) | lines with nested calls | Run → Debugging Actions |
| **Step Out** | runs to the end of the current method, stops back in the caller | you've seen enough of this method | Debug toolbar |
| **Run to Cursor** | runs until the line where your cursor is (a one-time breakpoint) | skip ahead without adding breakpoints | right-click a line, or Run → Debugging Actions |
| **Resume** | runs until the next breakpoint | | Debug toolbar (green ▶) |
| **Variables** | parameters, locals, `this` (Topic 3) | always | Threads & Variables tab |
| **Watches** | expressions you pin; re-evaluated at every pause | track something across steps (`project.Tasks.Count`) | right-click a variable → Add to Watches, or type in the field at the top of Variables |
| **Evaluate Expression** | runs **any** C# expression right now, in the paused context | test a hypothesis (`(double)done / total * 100`) | right-click in the editor → Evaluate Expression, or the field at the top of Variables |
| **Conditional breakpoint** | pauses only when a condition is true (`task.Id == 158`) | a loop of 300 items where 1 is bad | right-click the red dot → Condition |
| **Hit count** | pauses only on the Nth time | "fails on the 3rd call" | right-click the red dot → More… |
| **Logpoint / tracepoint** | prints a message **without pausing** and without changing code | you want a log line but don't want to edit code | right-click the red dot → More… → uncheck *Suspend*, enable *Log evaluated expression* |
| **Exception breakpoint** | pauses where an exception is **thrown**, even if caught (Topic 3) | "it fails somewhere" | Run → View Breakpoints → + → .NET Exception Breakpoint |
| **Frames (call stack)** | the chain of calls; click a frame to see **that** method's variables (Topic 2) | "who called this with these values?" | Threads & Variables tab |
| **Parallel Stacks** | all threads and where they are (Topic 4) | async / concurrency bugs | Parallel Stacks tab |

Menu names can differ slightly between Rider versions. If something isn't exactly where described, use **Help → Find Action** (Cmd+Shift+A) and type its name, e.g. "Evaluate Expression".

---

## 4. Debug Lab A

### Setup
1. `git pull`, then run `dotnet run playground/05-debug-lab.cs` once **without** the debugger and read the three symptoms:
   ```
   Bug report 1: Website redesign  2/4 done -> 0%     (expected 50%)
   Bug report 2: FAILED: IndexOutOfRangeException      (expected a list of codes)
   Bug report 3: Project 1 task count before: 4, after: 2   (expected 4 and 4)
   ```
2. For debugging, add **one line** temporarily to `Program.cs`, right before `app.Run();`:
   ```csharp
   await ProjectHub.Api.Labs.DebugLabA.RunAsync();
   ```
   and start the API with the **Debug** button. The lab runs first, then the API starts. Stop debugging when you're done.
3. **Rules:** no `Console.WriteLine`, no editing `DashboardReport.cs` until you've **found and verified** the cause in the debugger.

### Bug report 1: "The progress widget shows 0% for projects that are half done"
- **Symptom:** Website redesign has 2 of 4 tasks done but shows `0%`. Legacy import has 100 of 300 done and also shows `0%`.
- **Tools to use:** breakpoint, **Step Into / Smart Step Into**, **Evaluate Expression**, **Step Out**.
- **Do:**
  1. Put a breakpoint in `DashboardReport.GetProgressAsync` on the `result.Add(...)` line.
  2. When it stops for Website redesign, check `done` and `total` in Variables. Are the inputs correct?
  3. Step **into** the calculation (use Smart Step Into and pick it). Inside, use **Evaluate Expression** on parts of the formula. Which part becomes wrong?
  4. Form a hypothesis, and test a corrected expression with Evaluate Expression **before** changing any code. Does it give `50`?
  5. **Step Out** back to the caller.
- **Report back:** the line, *why* it produces 0 (name the C# concept), and the fix you verified with Evaluate.

### Bug report 2: "The task codes widget fails to load"
- **Symptom:** `IndexOutOfRangeException`. 300+ tasks, and the error message doesn't say which one.
- **Tools to use:** **exception breakpoint**, **Frames**, **conditional breakpoint**, Step Into.
- **Do:**
  1. Add a **.NET Exception Breakpoint** for `System.IndexOutOfRangeException` (as in Topic 3). Debug.
  2. Where does it stop? Look at `title`, `words`, `i` in Variables. What's unusual?
  3. In **Frames**, click the caller frame (`GetTaskCodesAsync`). Which `task` was being processed? Note its `Id`.
  4. Remove the exception breakpoint. Put a normal breakpoint on the `codes.Add(...)` line and make it **conditional**: `task.Id == <the id you found>`. Debug again. It should stop **only** for that one task out of 300+.
  5. **Step Into** `Initials` and step through the loop, watching `words[i]`.
- **Report back:** which task, what's special about its title, why that crashes, and how you'd fix it (and what the code for that title *should* be).

### Bug report 3: "After the Open work widget loads, done tasks vanish from the project page"
- **Symptom:** project 1 has 4 tasks before `GetOpenWorkAsync` runs and 2 after. A *read-only* report changed the data.
- **Tools to use:** breakpoint, **Watches**, Step Over.
- **Do:**
  1. Put a breakpoint in `GetOpenWorkAsync` on the line `var open = project.Tasks;`.
  2. Add two **Watches**: `project.Tasks.Count`, and `ReferenceEquals(open, project.Tasks)`.
  3. **Step Over** line by line, watching both. On which line does `project.Tasks.Count` change? What does the `ReferenceEquals` watch say, and why?
- **Report back:** the line, the C# concept behind it (think Topic 1 and Topic 3), and a fix. Bonus: which Topic 2 method would have avoided it?

### When you've found all three
Send me, for each bug: **where** (file + line), **why** (the concept), **how you found it** (which tools), and **the fix**. I'll apply the fixes, re-run the lab to confirm all three symptoms are gone, and then we do the CHECK questions.

---

## 5. CHECK: answer these in your own words (after the lab)

1. Why use a debugger instead of `Console.WriteLine` locally? When *are* logs the right tool?
2. Describe your debugging method in 4–5 steps.
3. Step Over vs Step Into vs Step Out vs Run to Cursor: when do you use each?
4. What's a conditional breakpoint, and when does it beat a normal one?
5. What does an exception breakpoint give you that a stack trace in the console doesn't?
6. Watches vs Evaluate Expression: what's the difference?
7. How do you use the Frames list to answer "who called this method with this value?"
8. For each lab bug: one sentence on the concept behind it.

---

## 6. Hints (only if you're stuck for more than 15 minutes)

<details>
<summary>Bug 1 hint</summary>

Evaluate `done / total` on its own. What are the types of `done` and `total`? What's `2 / 4` when both sides are `int`?
</details>

<details>
<summary>Bug 2 hint</summary>

Look at the exact characters in `title`. How many spaces are between the words, and what does `Split(' ')` produce for two spaces in a row?
</details>

<details>
<summary>Bug 3 hint</summary>

`var open = project.Tasks;` copies **what**, exactly? (Topic 1: reference types.)
</details>
