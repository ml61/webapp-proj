using Microsoft.AspNetCore.Mvc;

namespace ProjectHub.Api.Labs.Lifetimes;

// TOPIC 7 LAB: GET /api/labs/lifetimes. Call it twice and compare the ids.
[ApiController]
[Route("api/labs/lifetimes")]
public class LifetimesController(
    SingletonOperation singleton,
    ScopedOperation scoped,
    TransientOperation transient,
    LifetimeReporter reporter) : ControllerBase
{
    [HttpGet]
    public IActionResult Get() => Ok(new
    {
        controller = new { singleton = singleton.Id, scoped = scoped.Id, transient = transient.Id },
        reporter = reporter.Report(),
    });
}
