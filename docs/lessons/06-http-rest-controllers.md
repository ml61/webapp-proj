# Lesson 6: HTTP + REST, controllers, DTOs

**Roadmap:** Week 2, Topic 6. **Time:** about 2–3 h.
**Checkpoint:** GET / POST / PUT / DELETE work with **sensible status codes**.

**Files for this lesson:**
- `src/ProjectHub.Api/Controllers/ProjectsController.cs`: the API endpoints
- `src/ProjectHub.Api/Contracts/*.cs`: DTOs (request and response records) plus `ProjectMappings.cs`
- `src/ProjectHub.Api/Program.cs`: registers the service, configures JSON
- `src/ProjectHub.Api/Services/*`: new `UpdateAsync` / `DeleteAsync`; `Exceptions/ConflictException.cs`
- `src/ProjectHub.Api/ProjectHub.Api.http`: every request with its expected status code. Run them from Rider.
- Deleted: the `WeatherForecast` template files

---

## 1. HTTP in one table (you know this from `fetch`)

| Part | Request | Response |
|---|---|---|
| Line | **method** + **URL**: `POST /api/projects` | **status code**: `201 Created` |
| Headers | `Content-Type: application/json`, `Authorization: ...` | `Content-Type`, `Location: /api/projects/4` |
| Body | JSON the client sends | JSON the server returns |

In React you wrote the *client* side: `fetch(url, { method: 'POST', body: JSON.stringify(x) })`, then `if (!res.ok) ...`. Now you write the *server* side, and you decide which status code `res.status` will be.

## 2. REST: resources, URLs, verbs

**Resources are nouns, in the plural; the HTTP method is the verb.** The URL names *what*, the method says *what to do with it*.

| Method | URL | Meaning | Safe? | Idempotent? |
|---|---|---|---|---|
| `GET` | `/api/projects` | list | yes | yes |
| `GET` | `/api/projects/5` | read one | yes | yes |
| `POST` | `/api/projects` | create (server picks the id) | no | **no** |
| `PUT` | `/api/projects/5` | replace the editable fields | no | yes |
| `PATCH` | `/api/projects/5` | change some fields (not used yet) | no | not necessarily |
| `DELETE` | `/api/projects/5` | delete | no | yes |
| `POST` | `/api/projects/5/tasks` | create a task **inside** project 5 (nested resource) | no | no |

- **Safe:** doesn't change data. Browsers, caches and crawlers may call it freely.
- **Idempotent:** calling it **once or 5 times leaves the same final state**. `PUT` with the same body twice gives the same project. `DELETE` twice leaves it deleted (the second call returns 404, but the state is the same). `POST` twice creates **two** projects, or here, the second one gets 409. That's why a retry after a network timeout is safe for `PUT`/`DELETE` but risky for `POST`.
- Not REST-y: `POST /api/createProject`, `GET /api/deleteProject?id=5`. Verbs in URLs, and a GET that changes data.

## 3. Status codes (the checkpoint)

| Code | Name | When | In ProjectHub |
|---|---|---|---|
| **200** | OK | success with a body | GET, PUT |
| **201** | Created | a new resource was created. Add a **`Location`** header pointing to it | POST project, POST task |
| **204** | No Content | success, nothing to return | DELETE |
| **400** | Bad Request | the request is invalid: malformed JSON, missing field, rule broken by the input itself | empty name, missing `name`, broken JSON |
| 401 / 403 | Unauthorized / Forbidden | not logged in / not allowed | Topic 16 |
| **404** | Not Found | the resource (or route) doesn't exist | unknown id; `/api/projects/abc` |
| **409** | Conflict | valid request, but it **conflicts with the current state** | the name is already taken |
| **500** | Internal Server Error | **our** bug or infrastructure failure (unexpected) | an unhandled exception (Topic 12) |

**4xx = the client must change something. 5xx = the server has a problem.** That's the Topic 3 "expected vs unexpected" split again, now as HTTP: expected errors become 4xx, unexpected ones become 500.

**400 vs 409:** `"   "` is wrong no matter what's in the database → **400**. `"Mobile app"` is a perfectly valid name, but it's **taken right now** → **409**. Retrying the 400 can never work. The 409 could work after someone renames the other project.

## 4. How a request reaches our code

```
HTTP request → Kestrel (the web server) → middleware pipeline (Program.cs: HTTPS redirect, auth, ...)
            → routing: which controller action matches "POST /api/projects"?
            → model binding: JSON body → CreateProjectRequest, "5" in the URL → int id
            → [ApiController] validation: invalid → automatic 400, the action never runs
            → your action method → result (Ok, NotFound, ...) → JSON → HTTP response
```
Express analogy: `app.use(...)` middlewares, then `router.post('/api/projects', handler)`. In ASP.NET the "router" reads **attributes** on the controller.

## 5. The controller, line by line

```csharp
[ApiController]
[Route("api/projects")]
public class ProjectsController(IProjectService projects) : ControllerBase
```
- **`[ApiController]`** switches on API conventions:
  1. an invalid model gives an **automatic 400**, before your code runs
  2. error results become **ProblemDetails** JSON
  3. complex parameters come **from the body**, simple ones from the route or query
- **`[Route("api/projects")]`**: the base URL for every action in this class.
- **`ControllerBase`**: the base class with helpers like `Ok()`, `NotFound()`, `NoContent()`, `CreatedAtAction()`, `Problem()`. `Controller` (without "Base") adds HTML view support, which an API doesn't need.
- **`(IProjectService projects)`**: a primary constructor (Topic 3). ASP.NET **creates the controller for every request** and passes the registered `IProjectService` in. That's **dependency injection**, set up in `Program.cs` (section 8, more in Topic 7). The controller never calls `new ProjectService(...)`.

```csharp
[HttpGet("{id:int}")]
public async Task<ActionResult<ProjectResponse>> GetById(int id, CancellationToken cancellationToken)
{
    var project = await projects.GetByIdAsync(id, cancellationToken);
    return project is null ? NotFound() : Ok(project.ToResponse());
}
```
- **`[HttpGet("{id:int}")]`**: the method is GET and the route is `api/projects/{id}`. **`:int` is a route constraint**: `/api/projects/abc` doesn't match **any** action, so the result is a plain **404 with an empty body** (we saw it). Without the constraint, `abc` would reach the action and fail model binding instead, giving 400.
- **`int id`**: **model binding** takes `5` from the URL and converts it to `int`.
- **`CancellationToken cancellationToken`**: ASP.NET fills it with **`HttpContext.RequestAborted`**, which is cancelled when the client disconnects. That's the Topic 4 promise kept: we pass it down to the service.
- **`ActionResult<ProjectResponse>`**: "either a `ProjectResponse` (200) or another result (404, …)". The `<T>` documents the success type for OpenAPI. `Delete` returns plain **`IActionResult`** because it never has a body.
- `GetById` returning `null` → **404**: the Topic 3 "query returns null" decision maps naturally to HTTP.

```csharp
[HttpPost]
public async Task<ActionResult<ProjectResponse>> Create(CreateProjectRequest request, CancellationToken cancellationToken)
{
    try
    {
        var project = await projects.CreateAsync(request.Name, request.Description, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = project.Id }, project.ToResponse());
    }
    catch (ConflictException ex) { return Problem(detail: ex.Message, statusCode: StatusCodes.Status409Conflict); }
    catch (BusinessRuleException ex) { return Problem(detail: ex.Message, statusCode: StatusCodes.Status400BadRequest); }
}
```
- **`CreateProjectRequest request`**: bound **from the JSON body** (inferred by `[ApiController]`). `{"name": "Docs portal"}` maps to `Name` (JSON names are **camelCase**, matched case-insensitively).
- **`CreatedAtAction(nameof(GetById), new { id = project.Id }, body)`** returns **201** plus a header **`Location: http://localhost:5064/api/projects/4`**, built from the `GetById` route. `nameof` keeps it refactor-safe (Topic 3).
- **Catch order matters** (Topic 3): `ConflictException` derives from `BusinessRuleException`, so it must be caught **first**. Swapped, the compiler reports an error (the second catch would be unreachable).
- **`Problem(detail:, statusCode:)`** returns a **ProblemDetails** body (section 7).
- **The repeated try/catch in every action is deliberate for now.** You can see the pattern, and you can also see that it's repetitive. **Topic 12** moves it into **one global exception handler**, and the actions shrink to just the happy path.

The other actions follow the same pattern:
- `Update`: `PUT` → 200 / 400 / 404 / 409
- `Delete`: `DELETE` → 204 / 404
- `AddTask`: `POST {id}/tasks` → 201 / 400 / 404. Its `Location` points to the project, because there's no "get one task" endpoint yet.

## 6. DTOs: why the API never returns entities

**DTO = Data Transfer Object**: a class or record whose only job is to be the **shape of the data crossing the HTTP boundary**. Topic 1 already said it: *data moving across a boundary is a record*.

| Request DTOs (input) | Response DTOs (output) |
|---|---|
| `CreateProjectRequest(string Name, string? Description)` | `ProjectSummaryResponse(Id, Name, Description, CreatedAt, TaskCount, DoneCount)`: list items |
| `UpdateProjectRequest(string Name, string? Description)` | `ProjectResponse(Id, Name, Description, CreatedAt, Tasks)`: one project with tasks |
| `CreateTaskRequest(string Title)` | `TaskResponse(Id, ProjectId, Title, Status, CreatedAt)` |

Why not just use the `Project` entity for input and output?
1. **Security: "over-posting" / mass assignment.** If `POST` accepted a `Project`, a client could send `"id": 999` or `"createdAt": "2000-01-01"` and set fields it must never control. A request DTO contains **only what the client may set**.
2. **A stable contract.** The frontend depends on the JSON shape. Entities change with the database (Topic 10 adds EF things). DTOs let the two evolve separately: rename a column without breaking the React app.
3. **The right shape per use case.** The list has counts (small), the detail view has tasks (big). One entity can't be both.
4. **No leaks (Topics 3 and 5).** A DTO is a **new object**. Nobody outside the service ever gets a reference to the stored `Project`, so the "renamed by a caller" and "RemoveAll deleted data" bugs can't happen through the API.
5. **No accidental data exposure** (a future `PasswordHash` on a `User` entity never reaches JSON) and no **cycles** (a Project with Tasks pointing back to the Project would make the JSON serializer loop).

**Mapping** (`Contracts/ProjectMappings.cs`) uses **extension methods** (Topic 2): `project.ToResponse()`, `task.ToResponse()`, `project.ToSummaryResponse()`. It's plain, explicit code, easy to debug. Libraries like AutoMapper or Mapster do this by convention. Some teams use them; many prefer explicit mapping like ours. Follow your team's choice.

**Records** are a natural fit for DTOs: immutable, value equality, one line each (Topic 1).

## 7. JSON and ProblemDetails

- **System.Text.Json** turns objects into JSON with **web defaults**: property names in **camelCase** (`createdAt`), and `DateTime` in ISO 8601 (`"2026-09-01T09:00:00Z"`, where `Z` = UTC from Topic 1).
- **Enums:** by default `TaskItemStatus.Done` would be `2` in JSON. We added `JsonStringEnumConverter` in `Program.cs`, so it's `"Done"`. That's readable for the frontend, and reordering the enum later can't silently change the meaning of stored numbers.
- **ProblemDetails** (RFC 9457) is the **standard error body**, with content type `application/problem+json`:
  ```json
  {"type":"https://tools.ietf.org/html/rfc9110#section-15.5.10","title":"Conflict","status":409,
   "detail":"A project named 'WEBSITE REDESIGN' already exists.","traceId":"00-cc8f..."}
  ```
  `traceId` identifies the request in logs (Topic 17). The frontend can always read `status`/`title`/`detail` the same way, whatever the error.
- **Automatic 400 from `[ApiController]`.** With nullable reference types on, `string Name` (non-nullable) is treated as **required**. Missing `name` → 400 **before our action runs**, with an `errors` dictionary:
  ```json
  {"title":"One or more validation errors occurred.","status":400,"errors":{"Name":["The Name field is required."]}}
  ```
  Malformed JSON gets the same kind of response. Topic 12 adds proper validation rules (length, format).

## 8. `Program.cs`: registering the service

```csharp
builder.Services.AddControllers()
    .AddJsonOptions(options =>
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));

builder.Services.AddSingleton<IProjectService>(_ => new ProjectService(SampleData.CreateProjects()));
```
- `AddSingleton<IProjectService>(...)`: "whenever someone needs an `IProjectService`, give them **this one object**, created once for the app's lifetime". The controller's constructor asks for `IProjectService`, and ASP.NET hands it over.
- **Why a singleton here:** the data lives **in the service's list**. If every request got a new `ProjectService`, every request would start from the sample data again, and a created project would vanish on the next call. One shared object means one shared list, which is exactly why Topic 4's **`lock`** was needed: many requests use it in parallel.
- The controller depends on the **interface**: Topic 10 swaps in EF Core by changing this one registration line.
- **Topic 7** covers the three lifetimes (Singleton, Scoped, Transient) properly.

## 9. Service changes

- **`UpdateAsync(id, name, description)`:** validate → "database call" → under the lock: find (404), **`EnsureNameIsFree(name, exceptProjectId: id)`** (a project may keep its own name, but not take another's), then set the fields.
- **`DeleteAsync(id)`:** find (404) → remove. It throws `NotFoundException` because it's a command that can't be carried out (Topic 3).
- **`ConflictException : BusinessRuleException`:** duplicate names now throw this subtype, so the controller can send **409** instead of 400. Because it *derives* from `BusinessRuleException`, older code that catches `BusinessRuleException` (the Topic 3/4 demos) still works unchanged.
- **Refactor:** `ValidateName` and `EnsureNameIsFree` are shared by create and update, so the rule lives in one place.
- The Topic 3 demo's `LoggingProjectService` got pass-through `UpdateAsync`/`DeleteAsync`. An interface change forces **every implementation** to change: the compiler checks it (Topic 3).

**Known limitations (on purpose):**
- **Mapping happens outside the lock.** If one request updates or adds to a project while another is converting it to JSON, the second may read a half-changed project, or hit "Collection was modified" on `Tasks`. That's rare with in-memory data, and EF Core (Topic 10) removes it, because every request then gets **its own copies** loaded from the database.
- No paging, sorting or filtering on `GET /api/projects` (Topic 2's `Skip`/`Take` and the `Page<T>` from Topic 3 are ready for it). No `PATCH`. No endpoints to update or delete a single task yet.

## 10. What the API actually returns (run in the cloud container)

| Request | Status | Why |
|---|---|---|
| `GET /api/projects` | **200** | list of 3 summaries with `taskCount`/`doneCount` |
| `GET /api/projects/1` | **200** | project + 4 tasks, `"status": "Done"` as text |
| `GET /api/projects/999` | **404** | `GetByIdAsync` returned null → `NotFound()` (ProblemDetails, no detail) |
| `GET /api/projects/abc` | **404**, empty body | `:int` constraint: no action matched at all |
| `POST` `{"name":"Docs portal",...}` | **201** | `Location: http://localhost:5064/api/projects/4` |
| `POST` `{"name":"WEBSITE REDESIGN"}` | **409** | `ConflictException` (case-insensitive duplicate) |
| `POST` `{"name":"   "}` | **400** | `BusinessRuleException` from our rule |
| `POST` `{"description":"no name"}` | **400** | automatic: `"errors":{"Name":["The Name field is required."]}` |
| `POST` broken JSON | **400** | automatic: JSON parse error |
| `PUT /api/projects/4` new name | **200** | updated project returned |
| `PUT /api/projects/4` `{"name":"Mobile app"}` | **409** | another project has that name |
| `PUT /api/projects/999` | **404** | `NotFoundException` |
| `POST /api/projects/4/tasks` | **201** | `"status": "Todo"`, Location → project 4 |
| `POST /api/projects/999/tasks` | **404** | `NotFoundException` |
| `DELETE /api/projects/4` | **204** | no body |
| `DELETE /api/projects/4` again | **404** | already gone (state unchanged: idempotent) |

---

## 11. Try it in Rider

1. `git pull`. Start the API with **Run** or **Debug**, using the **http** profile (`http://localhost:5064`).
2. Open `src/ProjectHub.Api/ProjectHub.Api.http`. Click the **green arrow** next to a request. The response (status, headers, body) opens in a panel.
3. Run them **top to bottom**: the later ones use project 4, created by the POST.
4. Also open `http://localhost:5064/openapi/v1.json` in a browser. That's the machine-readable description of the API that ASP.NET generates from your controllers and DTOs. The React frontend will generate a typed client from it later.

## 12. DEBUG (Rider): watch the pipeline

1. **Debug** the API. Put a breakpoint on the first line inside `ProjectsController.Create`.
2. Send the **201** POST from the `.http` file. When it stops:
   - In Variables, expand `request`. That's the JSON body, already converted to a `CreateProjectRequest` record (model binding).
   - Look at `cancellationToken`. Is `IsCancellationRequested` false?
   - **Step Into** `CreateAsync`, then **Step Out** back. Step Over `CreatedAtAction` and look at the result object.
3. Send the **"no name"** POST (automatic 400). **Is your breakpoint hit?** Why not?
4. Send `GET /api/projects/abc` with a breakpoint in `GetById`. Is it hit? Why not, and why is the body empty?
5. **Break it:** in `Create`, swap the two `catch` blocks (put `BusinessRuleException` first) and build. What does the compiler say, and why? Then undo.
6. **Break it 2:** temporarily comment out the `JsonStringEnumConverter` line, restart, and `GET /api/projects/1`. What does `"status"` look like now? Then undo.

---

## 13. CHECK: answer these in your own words

1. What do 200, 201, 204, 400, 404, 409 and 500 mean? Give a ProjectHub example of each.
2. 400 vs 409: what's the difference? Why is a duplicate name 409?
3. What does "idempotent" mean? Which verbs are idempotent, and why does it matter for retries?
4. What does `CreatedAtAction` return, and what's the `Location` header for?
5. Why does the API use DTOs instead of returning the `Project` entity? Give at least three reasons.
6. What does `[ApiController]` do for you? (three things)
7. Where does the `CancellationToken` parameter of an action come from, and when is it cancelled?
8. Why is `ProjectService` registered as a **singleton**? What would go wrong if every request got a new one?
9. Why does `/api/projects/abc` give a 404 with an empty body, and not a 400?
10. What's ProblemDetails, and why is a standard error format useful for the frontend?
