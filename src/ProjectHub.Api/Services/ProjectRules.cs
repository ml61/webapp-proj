using ProjectHub.Api.Exceptions;

namespace ProjectHub.Api.Services;

// The business rules for names and titles, in ONE place. Used by both services (in-memory and EF Core)
// and by the database configuration (ProjectHubDbContext), so "max 100 characters" can never disagree
// between the C# check and the NVARCHAR(100) column.
public static class ProjectRules
{
    public const int MaxNameLength = 100;
    public const int MaxDescriptionLength = 1000;
    public const int MaxTitleLength = 200;

    public static string ValidateName(string name)
    {
        var trimmedName = name.Trim();

        if (trimmedName.Length == 0)
        {
            throw new BusinessRuleException("Project name is required.");
        }

        if (trimmedName.Length > MaxNameLength)
        {
            throw new BusinessRuleException($"Project name must be at most {MaxNameLength} characters.");
        }

        return trimmedName;
    }

    // New in Topic 10: the database column has a limit now. Without this check a long description
    // would reach SQL Server, fail there (error 2628, "String or binary data would be truncated"), and become a 500.
    public static void ValidateDescription(string? description)
    {
        if (description is { Length: > MaxDescriptionLength })
        {
            throw new BusinessRuleException($"Project description must be at most {MaxDescriptionLength} characters.");
        }
    }

    public static string ValidateTitle(string title)
    {
        var trimmedTitle = title.Trim();

        if (trimmedTitle.Length == 0)
        {
            throw new BusinessRuleException("Task title is required.");
        }

        if (trimmedTitle.Length > MaxTitleLength)
        {
            throw new BusinessRuleException($"Task title must be at most {MaxTitleLength} characters.");
        }

        return trimmedTitle;
    }
}
