namespace ProjectHub.Api.Labs.Lifetimes;

// Registered with AddTransient: a NEW object every time something asks for one.
public class TransientOperation : OperationBase;
