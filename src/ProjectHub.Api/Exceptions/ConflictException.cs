namespace ProjectHub.Api.Exceptions;

// A business rule broken because of the CURRENT STATE of the data (e.g. the name is already taken),
// not because the input itself is malformed. The API maps it to 409 Conflict.
// It derives from BusinessRuleException, so code that catches BusinessRuleException still catches it.
public class ConflictException(string message) : BusinessRuleException(message);
