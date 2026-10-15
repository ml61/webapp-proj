namespace ProjectHub.Api.Labs.Lifetimes;

// TOPIC 7 LAB: every object gets a random id when it is CREATED. Comparing ids shows whether
// two places received the same object or two different objects from the DI container.
public abstract class OperationBase
{
    public string Id { get; } = Guid.NewGuid().ToString()[..8];
}
