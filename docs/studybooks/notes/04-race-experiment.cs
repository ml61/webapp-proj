// Same check-then-act logic, once WITHOUT and once WITH a lock.
// Thread.Sleep(10) between check and add widens the gap so the race is easy to see.

Console.WriteLine($"Without lock: {Run(useLock: false)}");
Console.WriteLine($"With lock:    {Run(useLock: true)}");

static string Run(bool useLock)
{
    var names = new List<string>();
    var gate = new Lock();
    var results = new string[5];

    void Create(int i)
    {
        if (useLock)
        {
            lock (gate) { results[i] = CheckThenAdd(); }
        }
        else
        {
            results[i] = CheckThenAdd();
        }
    }

    string CheckThenAdd()
    {
        if (names.Contains("Race project")) return "rejected"; // check
        Thread.Sleep(10);                                        // the gap
        names.Add("Race project");                               // act
        return "created";
    }

    Parallel.For(0, 5, Create); // 5 threads at the same time
    return $"{string.Join(", ", results)}  -> {names.Count} project(s) named 'Race project'";
}
