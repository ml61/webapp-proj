namespace ProjectHub.Api.Labs.Lifetimes;

// Registered with AddScoped: ONE object per HTTP request (the request is the "scope").
public class ScopedOperation : OperationBase;
