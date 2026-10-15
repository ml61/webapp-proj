using System.Diagnostics;

namespace ProjectHub.Api.Middleware;

// Measures every request: adds an "X-Response-Time-Ms" header and writes one log line per request.
// Express equivalent: app.use(async (req, res, next) => { const start = Date.now(); await next(); ... })
public class RequestTimingMiddleware(RequestDelegate next, ILogger<RequestTimingMiddleware> logger)
{
    public const string HeaderName = "X-Response-Time-Ms";

    // Called once per request. "next" is the rest of the pipeline (routing, controllers, ...).
    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();

        // Headers can only be changed BEFORE the response starts being sent,
        // so the header is added in a callback that runs right before that moment.
        context.Response.OnStarting(() =>
        {
            context.Response.Headers[HeaderName] = stopwatch.ElapsedMilliseconds.ToString();
            return Task.CompletedTask;
        });

        try
        {
            await next(context); // everything after this middleware runs here
        }
        finally
        {
            // finally: log even if something further down threw an exception.
            logger.LogInformation(
                "HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs} ms",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds);
        }
    }
}
