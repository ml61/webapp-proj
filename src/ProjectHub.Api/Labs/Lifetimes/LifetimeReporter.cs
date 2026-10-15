namespace ProjectHub.Api.Labs.Lifetimes;

// A second consumer in the SAME request, so we can compare what it received with what the controller received.
public class LifetimeReporter(SingletonOperation singleton, ScopedOperation scoped, TransientOperation transient)
{
    public object Report() => new { singleton = singleton.Id, scoped = scoped.Id, transient = transient.Id };
}
