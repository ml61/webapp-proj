using System.Text.Json.Serialization;
using ProjectHub.Api.Data;
using ProjectHub.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddControllers()
    .AddJsonOptions(options =>
        // Enums as text in JSON: "status": "Todo" instead of "status": 0.
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

// ONE shared in-memory store for the whole app: every request gets the same ProjectService object,
// so data created by one request is visible to the next. Topic 7 explains lifetimes (Singleton/Scoped/Transient);
// Topic 10 replaces this with EF Core + SQL Server.
builder.Services.AddSingleton<IProjectService>(_ => new ProjectService(SampleData.CreateProjects()));

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
