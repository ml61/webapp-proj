using System.Text.Json.Serialization;
using Microsoft.Extensions.Options;
using ProjectHub.Api.Configuration;
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

// Settings: the "ProjectStore" section of appsettings*.json -> ProjectStoreOptions.
// ValidateOnStart: a bad value (e.g. -1) stops the app at startup instead of failing on some later request.
builder.Services.AddOptions<ProjectStoreOptions>()
    .BindConfiguration(ProjectStoreOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

// ONE shared in-memory store for the whole app (Singleton): data created by one request is visible to the next.
// A factory, because ProjectService needs values the container must look up first (options, logger).
builder.Services.AddSingleton<IProjectService>(serviceProvider =>
{
    var options = serviceProvider.GetRequiredService<IOptions<ProjectStoreOptions>>().Value;
    var logger = serviceProvider.GetRequiredService<ILogger<ProjectService>>();
    return new ProjectService(SampleData.CreateProjects(), TimeSpan.FromMilliseconds(options.SimulatedLatencyMs), logger);
});

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
