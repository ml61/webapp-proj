# ProjectHub

A learning project: going from React/TypeScript to C#/.NET backend, then fullstack.
It's a small project-management app: ASP.NET Core API + EF Core + SQL Server, with a React + TypeScript frontend later.

- Plan and status: [`docs/progress.md`](docs/progress.md)
- Lessons: [`docs/lessons/`](docs/lessons/)
- Interview prep: [`docs/interview-questions.md`](docs/interview-questions.md)

## Run
```bash
docker compose up -d                       # SQL Server (needed from week 2)
dotnet run --project src/ProjectHub.Api    # API
```
