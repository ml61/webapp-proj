using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using ProjectHub.Api.Data;
using ProjectHub.Api.Labs.Lifetimes;
using ProjectHub.Api.Middleware;
using ProjectHub.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// ---- 1. Register services in the DI container ("what can be injected, and how long it lives") ----

builder.Services.AddControllers()
    .AddJsonOptions(options =>
        // Enums as text in JSON: "status": "Todo" instead of "status": 0.
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

// Topic 10: the database. AddDbContext registers ProjectHubDbContext as SCOPED (one per request).
// The connection string comes from configuration: "ConnectionStrings:ProjectHub" (appsettings.Development.json,
// or an environment variable ConnectionStrings__ProjectHub in production). Missing = fail at startup (Topic 7).
var connectionString = builder.Configuration.GetConnectionString("ProjectHub")
    ?? throw new InvalidOperationException("Connection string 'ProjectHub' is missing (ConnectionStrings:ProjectHub).");

builder.Services.AddDbContext<ProjectHubDbContext>(options =>
{
    options.UseSqlServer(connectionString);

    // Development only: show parameter VALUES in the logged SQL. Never in production (it would log user data).
    if (builder.Environment.IsDevelopment())
    {
        options.EnableSensitiveDataLogging();
    }
});

// Scoped, because it uses the scoped DbContext. As a singleton it would capture ONE DbContext forever:
// a captive dependency (Topic 7), which ASP.NET refuses at startup in Development.
// The controller doesn't change at all: it only knows IProjectService (Topic 3's interface pays off).
builder.Services.AddScoped<IProjectService, ProjectService>();

// Topic 7 lab: the three lifetimes side by side (GET /api/labs/lifetimes).
builder.Services.AddSingleton<SingletonOperation>();
builder.Services.AddScoped<ScopedOperation>();
builder.Services.AddTransient<TransientOperation>();
builder.Services.AddScoped<LifetimeReporter>();

var app = builder.Build();

// ---- 2. The middleware pipeline: every request passes through these, in THIS order ----

// First, so it measures everything that comes after it.
app.UseMiddleware<RequestTimingMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
