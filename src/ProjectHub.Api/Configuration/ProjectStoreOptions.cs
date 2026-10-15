using System.ComponentModel.DataAnnotations;

namespace ProjectHub.Api.Configuration;

// Strongly typed settings for the in-memory project store, bound from the "ProjectStore" section of
// appsettings*.json (or environment variables like ProjectStore__SimulatedLatencyMs=500).
public class ProjectStoreOptions
{
    public const string SectionName = "ProjectStore";

    // How long each simulated "database call" waits. 0 = instant.
    [Range(0, 10_000)]
    public int SimulatedLatencyMs { get; set; }
}
