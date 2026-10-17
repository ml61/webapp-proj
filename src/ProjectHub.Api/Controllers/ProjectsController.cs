using Microsoft.AspNetCore.Mvc;
using ProjectHub.Api.Contracts;
using ProjectHub.Api.Exceptions;
using ProjectHub.Api.Services;

namespace ProjectHub.Api.Controllers;

// [ApiController]: automatic 400 for invalid request bodies, ProblemDetails for error responses,
// and [FromBody]/[FromRoute] inferred from the parameter types.
[ApiController]
[Route("api/projects")]
public class ProjectsController(IProjectService projects) : ControllerBase
{
    // GET /api/projects -> 200 with a list of summaries
    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<ProjectSummaryResponse>>> GetAll(CancellationToken cancellationToken)
    {
        var all = await projects.GetAllAsync(cancellationToken);
        return Ok(all.Select(p => p.ToSummaryResponse()).ToList());
    }

    // GET /api/projects/5 -> 200 with the project and its tasks, or 404
    [HttpGet("{id:int}")]
    public async Task<ActionResult<ProjectResponse>> GetById(int id, CancellationToken cancellationToken)
    {
        var project = await projects.GetByIdAsync(id, cancellationToken);
        return project is null ? NotFound() : Ok(project.ToResponse());
    }

    // POST /api/projects -> 201 Created + Location header, or 400 / 409
    [HttpPost]
    public async Task<ActionResult<ProjectResponse>> Create(CreateProjectRequest request, CancellationToken cancellationToken)
    {
        try
        {
            var project = await projects.CreateAsync(request.Name, request.Description, cancellationToken);
            return CreatedAtAction(nameof(GetById), new { id = project.Id }, project.ToResponse());
        }
        catch (ConflictException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status409Conflict);
        }
        catch (BusinessRuleException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status400BadRequest);
        }
    }

    // PUT /api/projects/5 -> 200 with the updated project, or 400 / 404 / 409
    [HttpPut("{id:int}")]
    public async Task<ActionResult<ProjectResponse>> Update(int id, UpdateProjectRequest request, CancellationToken cancellationToken)
    {
        try
        {
            var project = await projects.UpdateAsync(id, request.Name, request.Description, cancellationToken);
            return Ok(project.ToResponse());
        }
        catch (NotFoundException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status404NotFound);
        }
        catch (ConflictException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status409Conflict);
        }
        catch (BusinessRuleException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status400BadRequest);
        }
    }

    // DELETE /api/projects/5 -> 204 No Content, or 404
    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id, CancellationToken cancellationToken)
    {
        try
        {
            await projects.DeleteAsync(id, cancellationToken);
            return NoContent();
        }
        catch (NotFoundException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status404NotFound);
        }
    }

    // POST /api/projects/5/tasks -> 201 Created, or 400 / 404
    [HttpPost("{id:int}/tasks")]
    public async Task<ActionResult<TaskResponse>> AddTask(int id, CreateTaskRequest request, CancellationToken cancellationToken)
    {
        try
        {
            var task = await projects.AddTaskAsync(id, request.Title, request.DueDate, cancellationToken);
            // There is no "GET one task" endpoint yet, so Location points to the project that now contains it.
            return CreatedAtAction(nameof(GetById), new { id }, task.ToResponse());
        }
        catch (NotFoundException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status404NotFound);
        }
        catch (BusinessRuleException ex)
        {
            return Problem(detail: ex.Message, statusCode: StatusCodes.Status400BadRequest);
        }
    }
}
