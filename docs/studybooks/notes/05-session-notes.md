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
