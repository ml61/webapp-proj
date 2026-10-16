namespace ProjectHub.Api.Labs.Lifetimes;

// TOPIC 7 LAB: every object gets a random id when it is CREATED. Comparing ids shows whether
// two places received the same object or two different objects from the DI container.
public abstract class OperationBase
{
    // The constructor runs ONLY when an object is created: put a breakpoint here to count creations.
    // (A breakpoint on the Id line would also stop on every READ of Id, because that line holds the getter too.)
    protected OperationBase()
    {
        Id = Guid.NewGuid().ToString()[..8];
    }

    public string Id { get; }
}
