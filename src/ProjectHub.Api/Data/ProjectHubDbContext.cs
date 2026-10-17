using Microsoft.EntityFrameworkCore;
using ProjectHub.Api.Entities;
using ProjectHub.Api.Services;

namespace ProjectHub.Api.Data;

// The DbContext = one "session" with the database (one per HTTP request: registered as Scoped).
// It knows the model (which classes map to which tables), runs queries, and tracks changes until SaveChangesAsync.
// The options (provider = SQL Server, connection string) come from Program.cs through DI.
public class ProjectHubDbContext(DbContextOptions<ProjectHubDbContext> options) : DbContext(options)
{
    // A DbSet<T> = a table you can query with LINQ. "=> Set<T>()" instead of { get; set; }: no nullable warning.
    public DbSet<Project> Projects => Set<Project>();
    public DbSet<TaskItem> Tasks => Set<TaskItem>();

    // Conventions for ALL properties of a type: every DateTime / DateTime? goes through the UTC converter.
    protected override void ConfigureConventions(ModelConfigurationBuilder configurationBuilder)
    {
        configurationBuilder.Properties<DateTime>().HaveConversion<UtcDateTimeConverter>();
        configurationBuilder.Properties<DateTime?>().HaveConversion<UtcDateTimeConverter>();
    }

    // The model, by convention + this "Fluent API" configuration. Compare with sql/02-create-tables.sql:
    // conventions already give Id = PRIMARY KEY + IDENTITY, string = NOT NULL (string? = NULL), enum = INT,
    // ProjectId + Project.Tasks = FOREIGN KEY with an index. We only add what conventions can't guess.
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Project>(project =>
        {
            project.Property(p => p.Name).HasMaxLength(ProjectRules.MaxNameLength);              // NVARCHAR(100)
            project.Property(p => p.Description).HasMaxLength(ProjectRules.MaxDescriptionLength);

            // The Topic 3 rule, enforced by the database (Topic 8): a UNIQUE index on Name.
            // SQL Server's default collation is case-insensitive, so "Mobile app" = "MOBILE APP" here too.
            project.HasIndex(p => p.Name).IsUnique();

            // One project has many tasks; TaskItem.ProjectId is the foreign key.
            // Required relationship -> ON DELETE CASCADE by default: deleting a project deletes its tasks
            // (in Topic 8 our hand-written FK refused that delete: C5, error 547).
            project.HasMany(p => p.Tasks)
                .WithOne()
                .HasForeignKey(t => t.ProjectId);
        });

        modelBuilder.Entity<TaskItem>(task =>
        {
            // Table "Tasks" (the DbSet name) + Topic 8's CHECK constraint: only the three enum values.
            task.ToTable("Tasks", table => table.HasCheckConstraint("CK_Tasks_Status", "[Status] IN (0, 1, 2)"));
            task.Property(t => t.Title).HasMaxLength(ProjectRules.MaxTitleLength);
        });

        // Seed data: becomes INSERTs inside the migration. HasData can't take objects with navigation
        // properties filled in (project.Tasks), so we pass flat anonymous objects with the column values.
        var projects = SampleData.CreateProjects();
        modelBuilder.Entity<Project>().HasData(
            projects.Select(p => new { p.Id, p.Name, p.Description, p.CreatedAt }));
        modelBuilder.Entity<TaskItem>().HasData(
            projects.SelectMany(p => p.Tasks)
                .Select(t => new { t.Id, t.ProjectId, t.Title, t.Status, t.CreatedAt, t.DueDate }));
    }
}
