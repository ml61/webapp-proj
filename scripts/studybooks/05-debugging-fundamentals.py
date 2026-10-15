"""Study book for Topic 5: Debugging fundamentals (Debug Lab A).

Usage (from repo root):
  python3 scripts/studybooks/05-debugging-fundamentals.py docs/studybooks/05-debugging-fundamentals.pdf [fixed-output.txt]
Lab source is read from git: the buggy version (BUGGY_REV) and the fixed version (FIXED_REV).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

OUT = sys.argv[1]
FIXED_OUT = sys.argv[2] if len(sys.argv) > 2 else None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUGGY_REV = "95d4042"   # lab as handed out (3 planted bugs)
FIXED_REV = "129f691"   # lab after the fixes


def git_show(rev, rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def method(source, signature):
    """Cut one method (from its signature line to the matching closing brace) out of a C# file."""
    lines = source.splitlines()
    start = next(i for i, l in enumerate(lines) if signature in l)
    indent = len(lines[start]) - len(lines[start].lstrip())
    depth, out = 0, []
    for l in lines[start:]:
        out.append(l[indent:] if len(l) >= indent else l)
        depth += l.count("{") - l.count("}")
        if depth == 0 and "{" in "".join(out):
            break
    return "\n".join(out)


BUGGY = git_show(BUGGY_REV, "src/ProjectHub.Api/Labs/DashboardReport.cs")
FIXED = git_show(FIXED_REV, "src/ProjectHub.Api/Labs/DashboardReport.cs")
SCREENSHOT = os.path.join(ROOT, "docs/studybooks/notes/img/rider-conditional-breakpoint.png")

S = Story()

# ---------------------------------------------------------------- COVER
S += cover("Study book", "Topic 5: Debugging fundamentals (Debug Lab A)",
           "ProjectHub learning track: React/TypeScript to C#/.NET backend. Week 1, topic 5 of 20.")
S += NOTE([
    "**What this lesson is about.** Finding bugs **without `Console.WriteLine`**: a repeatable method (reproduce, locate, hypothesize, verify, fix, re-run) "
    "and the Rider toolbox (Step Into/Over/Out, Smart Step Into, Run to Cursor, Watches, Evaluate Expression, conditional breakpoints, "
    "exception breakpoints, Frames, logpoints).",
    "**What you did.** Debug Lab A: a `DashboardReport` with **three planted bugs** and a runner that reproduces three bug reports on realistic data "
    "(300 imported tasks). You found all three in Rider; the fixes were then applied and verified.",
    "**The three bugs**, each tied to an earlier topic: **integer division** (C# types), **an empty string from a double space** in imported data "
    "(defensive reading), **a copied reference** that let a read-only report delete data (topics 1, 2, 3).",
    "**Bonus gotchas found on the way:** `Math.Round` uses banker's rounding; `dotnet run file.cs` can run a **stale cached build**.",
], "Brief overview")
S += H2("Contents")
S += TABLE([
    ["Part", "What is inside"],
    ["1", "Why a debugger instead of Console.WriteLine"],
    ["2", "The debugging method"],
    ["3", "The Rider toolbox (with the breakpoint popup from your Rider)"],
    ["4", "Lab setup: files, data, how to run, how to debug"],
    ["5", "Bug 1: integer division"],
    ["6", "Bug 2: the double space in task 158"],
    ["7", "Bug 3: the read-only report that deleted data"],
    ["8", "Two bonus gotchas: banker's rounding and stale builds"],
    ["9", "Your answers, corrections, interview Q&A"],
    ["10", "Summary, checklist, what comes next"],
], [20, 150])
S += PageBreak()

# ---------------------------------------------------------------- PART 1-2
S += H1("Part 1. Why a debugger instead of Console.WriteLine")
S += TABLE([
    ["Console.WriteLine / console.log", "Debugger"],
    ["guess **in advance** what to print", "see **every** variable at the paused moment"],
    ["change code, rebuild, rerun for every new question", "ask new questions **while paused** (Watches, Evaluate Expression)"],
    ["shows values, not **how you got here**", "the **call stack** shows the chain of calls"],
    ["prints every loop iteration (noise)", "**conditional breakpoints** stop only on the interesting one"],
    ["leftover prints get committed", "nothing to clean up"],
], [85, 85])
S += P("**Logs are for production**, where you cannot attach a debugger (topic 17). Locally you use the debugger. Your answer: 'we don't need to know the place in advance, we have lots of tools; logs are for prod' (right).")

S += H1("Part 2. The method")
S += numbered([
    "**Reproduce** the bug reliably (the lab runner does this).",
    "**Locate** where the wrong value first appears: start at the symptom, walk backwards (call stack, Step Into) until one line is right and the next is wrong.",
    "**Hypothesize** in one sentence why it is wrong.",
    "**Verify the hypothesis in the debugger before changing code** (Evaluate Expression with the corrected formula).",
    "**Fix**, then **re-run the reproduction**; later a **unit test** keeps the bug from coming back (topic 13).",
])
S += WARN(["Your answer listed practical steps (run, exception breakpoint, precise breakpoints, step into) — that is the **locate** phase only. "
           "Missing: hypothesize, **verify before changing code**, fix, re-run. Verifying first is what separates debugging from guessing; you did it in bug 1."])

# ---------------------------------------------------------------- PART 3
S += H1("Part 3. The Rider toolbox")
S += TABLE([
    ["Tool", "What it does", "Use when"],
    ["Breakpoint", "pauses **before** a line runs", "you know roughly where to look"],
    ["Step Over", "runs the line, stops at the next one in the same method", "the call's internals don't matter"],
    ["Step Into", "enters the method called on the line", "the bug may be inside that call"],
    ["Smart Step Into", "choose **which** call to enter on a line with several", "`result.Add(new X(..., Calc(a, b)))`"],
    ["Step Out", "runs to the end of the method, stops in the caller", "seen enough here"],
    ["Run to Cursor", "runs to the cursor's line: a **one-time breakpoint**", "skip ahead (e.g. past a 300-item loop)"],
    ["Watches", "**pinned** expressions, re-evaluated **automatically** at every pause", "track a value across steps (`project.Tasks.Count`)"],
    ["Evaluate Expression", "runs any C# expression now, in the paused context", "test a hypothesis or a fix"],
    ["Conditional breakpoint", "pauses only when a condition is true", "1 bad item in a big loop"],
    ["Hit count", "pauses only on the Nth hit", "'fails on the 3rd call'"],
    ["Logpoint / tracepoint", "prints without pausing and without editing code", "a log line without touching code"],
    ["Exception breakpoint", "pauses at the **throw**, locals alive, **even if caught later**", "'it fails somewhere'"],
    ["Frames (call stack)", "click a caller frame to see **its** variables", "'who called this with this value?'"],
    ["Parallel Stacks", "all threads and where they are", "async / concurrency (topic 4)"],
], [40, 76, 54])
S += P("Your Rider's menu for exception breakpoints: **Run > Stop on Exception...** (other versions: Run > View Breakpoints > + > .NET Exception Breakpoint). "
       "If a menu name differs: **Help > Find Action** (Cmd+Shift+A) and type the feature name.")
S += RIDER_BREAKPOINT_TIP(SCREENSHOT)

# ---------------------------------------------------------------- PART 4
S += PageBreak()
S += H1("Part 4. Lab setup")
S += TABLE([
    ["File", "Role"],
    ["`src/ProjectHub.Api/Labs/DashboardReport.cs`", "report service for a future dashboard: Progress, Task codes, Open work widgets. Had 3 planted bugs (now fixed, marked 'LAB FIX')"],
    ["`src/ProjectHub.Api/Labs/DebugLabA.cs`", "runner: builds lab data and reproduces the three bug reports (not buggy)"],
    ["`playground/05-debug-lab.cs`", "runs the lab without the debugger"],
], [70, 100])
S += bullets([
    "**Lab data:** the sample projects + project 4 'Legacy import' with **300 tasks** (ids 8-307, every 3rd Done) 'copied from the old tracker'. "
    "Task **158** has the title `\"Migrate  legacy reports\"` with a **double space**.",
    "**See the symptoms:** `dotnet run --no-cache playground/05-debug-lab.cs`.",
    "**Debug:** temporarily add `await ProjectHub.Api.Labs.DebugLabA.RunAsync();` to `Program.cs` before `app.Run();`, start with **Debug**.",
    "**Rules:** no `Console.WriteLine`; don't edit the buggy file before the cause is found and verified.",
])
S += CODE("""
=== Bug report 1: 'The progress widget shows 0% for projects that are half done' ===
  Website redesign     2/4   done -> 0%
  Mobile app           0/3   done -> 0%
  Internal tools       0/0   done -> 0%
  Legacy import      100/300 done -> 0%

=== Bug report 2: 'The task codes widget fails to load' ===
  FAILED: IndexOutOfRangeException: Index was outside the bounds of the array.

=== Bug report 3: 'After the Open work widget loads, done tasks vanish from the project page' ===
  Project 1 task count before the widget: 4, after: 2
""", "The symptoms (before the fixes):")

# ---------------------------------------------------------------- PART 5
S += H1("Part 5. Bug 1: 0% progress (integer division)")
S += CODE(method(BUGGY, "private static int CalculatePercent"), "Buggy code (as handed out):")
S += H3("How it was found")
S += numbered([
    "Breakpoint on `result.Add(...)` in `GetProgressAsync`; for Website redesign the inputs were correct: `done = 2`, `total = 4`.",
    "**Smart Step Into** `CalculatePercent`; **Evaluate Expression** on parts of the formula: `done / total` gives `0`.",
    "Your reaction: 'WTF, 50 isn't int? WTF this didn't work done / total * 100?!' — that moment **is** the finding.",
])
S += H3("Why")
S += CODE("""
done / total * 100        // evaluated left to right
= (2 / 4) * 100           // int / int = INTEGER division: the fraction is cut off
= 0 * 100
= 0
""")
S += P("50 **is** an int; the problem is the intermediate step. When **both operands of `/` are int**, C# does integer division and **truncates toward zero** "
       "(`2 / 4 = 0`, `7 / 2 = 3`, `-7 / 2 = -3`, `299 / 300 = 0`). JS has one number type (double), so `2 / 4` is `0.5`.")
S += TABLE([
    ["Evaluate", "Result", "Why"],
    ["`2 / 4`", "`0`", "int / int"],
    ["`2 / 4.0`", "`0.5`", "one side is a double"],
    ["`2 * 100 / 4`", "`50`", "multiply first"],
    ["`100 * 100 / 300`", "`33`", "10000 / 300 truncated"],
    ["`(int)Math.Round(100 * 100.0 / 300)`", "`33`", "double math, then round"],
], [70, 30, 70])
S += CODE(method(FIXED, "private static int CalculatePercent"), "Fixed code:")
S += P("`100.0` makes it double math; `MidpointRounding.AwayFromZero` makes 12.5% show as 13% (see Part 8). The alternative `done * 100 / total` stays int but truncates (66.67 -> 66).")

# ---------------------------------------------------------------- PART 6
S += PageBreak()
S += H1("Part 6. Bug 2: the crash in 1 of 300 tasks")
S += CODE(method(BUGGY, "private static string Initials"), "Buggy code:")
S += H3("How it was found")
S += numbered([
    "Exception breakpoint for `System.IndexOutOfRangeException` (**Run > Stop on Exception...**). Rider stopped in `Initials`, on `words[i][0]`, although the runner **catches** the exception.",
    "Variables: `title = \"Migrate  legacy reports\"`, `words = [\"Migrate\", \"\", \"legacy\", \"reports\"]`, `i = 1`.",
    "**Frames:** clicked the caller frame `GetTaskCodesAsync` and read `task.Id = 158`.",
    "Conditional breakpoint on `codes.Add(...)` with `task.Id == 158` (your screenshot in Part 3): the debugger stopped **once** out of 300+ tasks; Step Into `Initials`.",
])
S += H3("Why")
S += P("Your diagnosis: 'double space, so after Split one element is an empty string, which has no length' (right). `\"\"[0]` has no character 0, so `IndexOutOfRangeException`.")
S += CODE(method(FIXED, "private static string Initials"), "Fixed code (the solution you asked for):")
S += bullets([
    "`StringSplitOptions.RemoveEmptyEntries` drops the empty pieces (JS: `title.split(' ').filter(Boolean)`).",
    "`words.Length == 0 ? \"?\"` guards a title made only of spaces.",
    "`string.Concat(words.Select(w => char.ToUpperInvariant(w[0])))`: the LINQ version of the loop (topic 2): map each word to its first letter, join them.",
    "Result: `\"Migrate  legacy reports\"` (#158) -> **`MLR-158`**.",
])
S += OK(["`ProjectService.CreateAsync` validates titles, but task 158 never went through it: it came from an **import**. "
         "Data from imports, databases and other systems does not always pass your validation: read it **defensively**, and clean it at the import boundary."],
        "The bigger lesson")

# ---------------------------------------------------------------- PART 7
S += H1("Part 7. Bug 3: the read-only report that deleted data")
S += CODE(method(BUGGY, "public async Task<Dictionary<string, List<TaskItem>>> GetOpenWorkAsync"), "Buggy code:")
S += H3("How to find it")
S += numbered([
    "Breakpoint on `var open = project.Tasks;`.",
    "**Watches:** `project.Tasks.Count` and `ReferenceEquals(open, project.Tasks)`.",
    "Step Over line by line: `ReferenceEquals` is **true**, and `project.Tasks.Count` flips from **4 to 2** exactly on the `RemoveAll` line.",
])
S += H3("Why")
S += P("`var open = project.Tasks;` copies the **reference**, not the list (topic 1: reference types). `open` and `project.Tasks` are two names for **the same list**, "
       "so `RemoveAll` deleted tasks from the service's real data. Topic 3's 'entities leak' warning came true; topic 2's `Where` would have avoided it because it builds a **new** sequence.")
S += CODE(method(FIXED, "public async Task<Dictionary<string, List<TaskItem>>> GetOpenWorkAsync"), "Fixed code:")
S += WARN(["Your answer 'RemoveAll was called on the original project.Tasks' said **what** happened. In the interview say **why**: "
           "'`var open = project.Tasks` copied the reference, not the list, so `RemoveAll` on `open` removed tasks from the service's real list.' "
           "You watched the count 'with your eyes'; a **Watch** would have shown the change automatically."])
if FIXED_OUT and os.path.exists(FIXED_OUT):
    S += CODE(open(FIXED_OUT, encoding="utf-8").read(), "Lab output after all three fixes:")

# ---------------------------------------------------------------- PART 8
S += PageBreak()
S += H1("Part 8. Two bonus gotchas found while fixing")
S += H2("8.1 Math.Round is banker's rounding")
S += CODE("""
Math.Round(12.5)                                 = 12   <- !
Math.Round(13.5)                                 = 14
Math.Round(12.5, MidpointRounding.AwayFromZero)  = 13
""")
S += P("By default .NET rounds an exact `.5` to the nearest **even** number (`MidpointRounding.ToEven`, 'banker's rounding'). JS `Math.round(12.5)` gives 13. "
       "Use `MidpointRounding.AwayFromZero` for 'school rounding'. It matters for percentages and money.")
S += H2("8.2 A stale build ran old code")
S += P("After the fixes, `dotnet run playground/05-debug-lab.cs` still printed **all three bugs**, although the fixes were in the file. "
       "The file-based app reused a **cached build**: the playground file itself had not changed, so it did not rebuild the `src/` code it references. "
       "`dotnet run --no-cache ...` rebuilt and showed the fixed output.")
S += bullets([
    "All playground headers, lessons and CLAUDE.md now use `dotnet run --no-cache playground/...`.",
    "**Debugging lesson:** when behaviour does not match the code you are reading, **suspect a stale build first** (frontend equivalent: stale cache, dev server not reloaded).",
])

# ---------------------------------------------------------------- PART 9
S += H1("Part 9. Your answers, corrections, interview Q&A")
S += H2("9.1 CHECK round 1 and re-check")
S += TABLE([
    ["Question", "Your answer", "Complete answer"],
    ["1. Debugger vs Console.WriteLine", "no need to know the place in advance; many tools; logs are for prod (right)", "+ ask new questions while paused; see how you got here (call stack)"],
    ["2. The method", "run, exception breakpoint, precise breakpoints, step into (locate only)", "reproduce, locate, hypothesize, **verify**, fix, re-run"],
    ["3. Over / Into / Out / Run to Cursor", "first three right; Run to Cursor 'doesn't matter' (**wrong**); re-check: one-time breakpoint to skip ahead (right)", "lab example: cursor on `return codes;` skips the loop"],
    ["4. Conditional breakpoint", "triggers only when the condition is true; e.g. id 158 in a 300-item loop (right)", ""],
    ["5. Exception breakpoint vs console", "'see all variables' / re-check: stops at the throw with locals alive (half)", "+ stops **even if the exception is caught later** (the runner caught bug 2)"],
    ["6. Watch vs Evaluate", "Evaluate right; Watch 'didn't use, watched with eyes'", "Watch = **pinned** expression re-evaluated **automatically** at every step"],
    ["7. Frames", "'not interesting'", "you **did** it in bug 2: click the caller frame to see its variables (task.Id 158)"],
    ["8. Concepts", "int/int 'rounded down'; double space; mutated original data", "integer division **truncates toward zero**; empty string from Split; **copied reference**"],
], [36, 70, 64])
S += H2("9.2 Interview questions with model answers")
qa = [
    ("How do you debug a bug locally?", "Reproduce it, locate where the value first goes wrong (breakpoints, call stack, Step Into), form a hypothesis, verify it in the debugger (Evaluate), fix, re-run the reproduction (and add a test)."),
    ("Why not Console.WriteLine?", "You must guess in advance and rebuild for every question; the debugger shows all state, the call stack, and lets you ask new questions while paused. Logs are for production."),
    ("Step Over vs Step Into vs Step Out vs Run to Cursor?", "Over: next line in this method. Into: enter the called method. Out: finish this method, back to the caller. Run to Cursor: one-time breakpoint at the cursor to skip ahead."),
    ("What is a conditional breakpoint?", "A breakpoint that pauses only when a condition is true, e.g. task.Id == 158 inside a loop of 300 items."),
    ("What does an exception breakpoint give you?", "It stops at the throw with all locals alive, even if the exception is caught later; a console stack trace has no variable values."),
    ("Watch vs Evaluate Expression?", "Watch: pinned expression re-evaluated at every step. Evaluate: a one-off expression run now, to test a hypothesis or a fix."),
    ("How do you find out who called a method with a bad value?", "Frames / call stack: click the caller frame to see its variables."),
    ("What is a logpoint (tracepoint)?", "A breakpoint that logs a message without pausing and without editing code (uncheck Suspend execution, add a log message)."),
    ("What is 2 / 4 in C#? Why?", "0: int / int is integer division, truncating toward zero. Use a double operand (2 / 4.0) or multiply first."),
    ("What does Math.Round(2.5) return?", "2: banker's rounding (to even) by default; use MidpointRounding.AwayFromZero for 3."),
    ("How can Split(' ') cause a crash?", "Consecutive spaces produce empty strings; indexing \"\"[0] throws. Use StringSplitOptions.RemoveEmptyEntries."),
    ("Why did a read-only report delete data?", "`var open = project.Tasks` copied the reference to the same list; RemoveAll changed the original. Use Where (new sequence) or copy the list."),
    ("Why validate or read data defensively even if the service validates input?", "Data can enter by other paths (imports, database, other systems) that bypass the service's validation."),
    ("The code looks fixed but the old behaviour remains. First suspect?", "A stale build or cache: force a rebuild (e.g. dotnet run --no-cache)."),
]
for q, a in qa:
    S += QA(q, a)

# ---------------------------------------------------------------- PART 10
S += PageBreak()
S += H1("Part 10. Summary")
S += OK([
    "**Method:** reproduce, locate, hypothesize, **verify in the debugger**, fix, re-run.",
    "**Tools:** Step Over/Into/Out, Smart Step Into, Run to Cursor, **Watches** (pinned, automatic), **Evaluate Expression** (test a fix while paused), "
    "**conditional breakpoints**, hit count, logpoints, **exception breakpoints** (stop at the throw, even if caught), **Frames** (caller's variables).",
    "**Bug 1:** int / int truncates: `(2 / 4) * 100 = 0`. Fix with double math + `MidpointRounding.AwayFromZero`.",
    "**Bug 2:** `Split(' ')` on a double space gives `\"\"`; `\"\"[0]` throws. Fix with `RemoveEmptyEntries`. Imported data skips your validation.",
    "**Bug 3:** `var open = project.Tasks` copies a reference; `RemoveAll` mutated the real data. Fix with `Where`.",
    "**Gotchas:** `Math.Round` is banker's rounding; a stale build can run old code (`--no-cache`).",
], "Key takeaways")
S += H2("Checklist: can you do this without notes?")
S += bullets([
    "Explain the debugging method in 5-6 steps, including 'verify before changing code'.",
    "Set a conditional breakpoint and an exception breakpoint in Rider.",
    "Use Frames to find which caller passed a bad value.",
    "Use a Watch to see on which line a value changes.",
    "Explain each lab bug in one sentence (concept + fix).",
    "Explain banker's rounding and when to use AwayFromZero.",
])
S += H2("What comes next: Week 2, Topic 6 (HTTP + REST, controllers)")
S += P("The first real API: routes, HTTP verbs, status codes, **DTOs** (which finally fix the 'entities leak' from topics 3 and 5), and controllers that call "
       "`IProjectService` with `async` and the request's `CancellationToken`. Checkpoint: GET/POST/PUT/DELETE work with sensible status codes.")

build(OUT, S, "ProjectHub study book | Topic 5: Debugging fundamentals", "ProjectHub study book: Topic 5, Debugging fundamentals")
print("ok", OUT)
