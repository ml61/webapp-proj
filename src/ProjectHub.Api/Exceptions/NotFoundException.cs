namespace ProjectHub.Api.Exceptions;

// Thrown when a requested entity does not exist. Topic 12 maps it to HTTP 404.
public class NotFoundException(string entityName, object key)
    : Exception($"{entityName} with id '{key}' was not found.")
{
    public string EntityName { get; } = entityName;
    public object Key { get; } = key;
}
