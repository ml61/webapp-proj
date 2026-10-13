namespace ProjectHub.Api.Exceptions;

// Thrown when a request breaks a business rule (an EXPECTED error, caused by the caller's input).
// Topic 12 maps it to an HTTP 4xx response.
public class BusinessRuleException(string message) : Exception(message);
