# Topic 5: notes for the study book (questions, corrections, requests)

- Lab design (Debug Lab A): src/ProjectHub.Api/Labs/DashboardReport.cs has 3 planted bugs; DebugLabA.cs reproduces them
  with lab data = SampleData + "Legacy import" project (300 tasks, every 3rd Done; task i=150 -> Id 158 has the title
  "Migrate  legacy reports" with a DOUBLE space).
  Bug 1: CalculatePercent `done / total * 100` -> integer division -> 0% (2/4 -> 0). Fix: `done * 100 / total` or
         `(int)Math.Round(done * 100.0 / total)`. Tools: Smart Step Into, Evaluate Expression, Step Out.
  Bug 2: Initials: `title.Split(' ')` on a double space gives an empty string, `words[i][0]` -> IndexOutOfRangeException.
         Fix: `Split(' ', StringSplitOptions.RemoveEmptyEntries)` (+ guard for empty titles). Tools: exception breakpoint,
         Frames (caller -> task.Id 158), conditional breakpoint `task.Id == 158`, Step Into.
  Bug 3: GetOpenWorkAsync: `var open = project.Tasks;` copies the REFERENCE (topic 1) -> RemoveAll mutates the service's
         real list (topic 3 entity leak, topic 2 Where vs RemoveAll). Fix: `project.Tasks.Where(t => t.Status != Done)
         .OrderByDescending(...).ToList()`. Tools: Watches (Count, ReferenceEquals), Step Over.
- Symptoms in the cloud run: 0% for all (2/4, 100/300); FAILED: IndexOutOfRangeException; project 1 tasks 4 -> 2.
- **Bug 1, user's reaction:** "WTF 50 isn't int? WTF this didn't work done / total * 100 ???" -> found it.
  Explanation: 50 IS an int; the problem is the intermediate step. Left to right: (2 / 4) * 100; int / int = integer
  division that TRUNCATES (not rounds): 2/4 = 0, 7/2 = 3, 299/300 = 0; then 0 * 100 = 0. JS has one number type
  (double) so 2/4 = 0.5. Evaluate table: 2/4 -> 0; 2/4.0 -> 0.5; 2*100/4 -> 50; 100*100/300 -> 33;
  (int)Math.Round(100*100.0/300) -> 33. Fixes: `done * 100 / total` (truncates 66.67 -> 66) or
  `(int)Math.Round(done * 100.0 / total)` (rounds -> 67, preferred).
- **User request:** note the Rider breakpoint popup (screenshot docs/studybooks/notes/img/rider-conditional-breakpoint.png)
  for this study book AND the previous one (added to topic 4 Part 10 as "Rider tip, added later" via
  common.RIDER_BREAKPOINT_TIP). Right-click the red dot -> "Line breakpoint" popup: Enabled; Suspend execution
  (unchecked + log message in More = logpoint/tracepoint); Condition (`task.Id == 158`, history dropdown, expand
  editor); More (Shift+Cmd+F8) = full breakpoint dialog (hit count, log message); Done.
  -> Use RIDER_BREAKPOINT_TIP in the topic 5 study book (bug 2 section).
- Bug 2 progress: user found the failing task via Frames: Id 158, and set the conditional breakpoint on the
  `codes.Add(...)` line with `task.Id == 158`.
- Rider menu in the user's version: exception breakpoints via **Run > Stop on Exception...** (topic 3 + 5 docs fixed).
- **Lab results (user):** bug 1 understood ("weird for a JS dev"); bug 2: "Migrate  legacy reports" has a double space,
  Split gives an empty string with no [0]; asked for the solution. Bug 3: RemoveAll on the original project.Tasks.
  Missing in bug 3: WHY -> `var open = project.Tasks` copies the reference (topic 1), same list, ReferenceEquals true;
  topic 3 entity leak; topic 2 Where builds a new sequence. Bug 1 wording: integer division truncates toward zero
  (-7 / 2 = -3), not "rounds down".
- **Bug 2 solution given:** `Split(' ', StringSplitOptions.RemoveEmptyEntries)`; `words.Length == 0 ? "?"`;
  `string.Concat(words.Select(w => char.ToUpperInvariant(w[0])))` -> "MLR-158". Lesson: imported/DB data does not pass
  through your validation; be defensive when reading; clean data at the import boundary.
- **Fixes applied** (marked "LAB FIX" in DashboardReport.cs). Bug 1 final fix:
  `(int)Math.Round(done * 100.0 / total, MidpointRounding.AwayFromZero)`. GOTCHA: Math.Round default is banker's rounding
  (MidpointRounding.ToEven): Math.Round(12.5) = 12, Math.Round(13.5) = 14, with AwayFromZero 12.5 -> 13.
  Verified output: 2/4 -> 50%, 100/300 -> 33%; 307 codes, task 158 -> MLR-158; project 1 tasks 4 -> 4.
- **Second real gotcha found while verifying:** `dotnet run playground/X.cs` reused a CACHED build after src/ changed
  (the playground file itself had not changed) and printed the OLD buggy output although the fixes were in the file.
  `dotnet run --no-cache ...` rebuilt and showed the fixed output. All playground headers, lessons and CLAUDE.md now use
  `--no-cache`. Lesson: when behaviour doesn't match the code, suspect a stale build first.
- **CHECK round 1:** 1 right (+ ask new questions while paused, see how you got there). 2 practical steps but only the
  "locate" phase -> full method reproduce, locate, hypothesize, verify (Evaluate), fix, re-run (unit test later).
  3 Over/Into/Out right; Run to Cursor WRONG ("doesn't matter") -> runs to the cursor line as a one-time breakpoint,
  to skip ahead (e.g. past a loop). 4 right. 5 half -> stops at the throw with all locals alive, even if caught later
  (runner caught bug 2 -> console showed only FAILED). 6 Evaluate right; Watch unknown ("watched with eyes") ->
  pinned expression re-evaluated at every step (project.Tasks.Count would flip 4 -> 2 on RemoveAll).
  7 "not interesting" -> user actually DID it in bug 2 (clicked the caller frame, found task.Id 158).
