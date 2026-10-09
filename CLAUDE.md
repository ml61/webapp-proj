# ProjectHub: learning C#/.NET backend (and fullstack)

## Who I am and why this repo exists
- Experienced React + TypeScript frontend developer moving to fullstack at my company (backend is C#/.NET).
- My teamlead gave me a roadmap: "React/TypeScript -> C#/.NET Backend" (4-week track, 2-3 h/day).
  The topic list and checkpoints are in `docs/progress.md`.
- After the roadmap my teamlead will interview me on it, and only then let me into our real (complex) backend.
- Final goals: (1) pass the interview on everything in the readiness checklist, (2) a finished fullstack app:
  ProjectHub API (ASP.NET Core + EF Core + SQL Server) + React/TypeScript frontend in `web/`.

## How Claude must work in this repo: TUTOR MODE
- **I write the domain code. Claude does not write it for me.** Claude explains, sets exercises, reviews, and asks questions.
- Claude may write setup/boilerplate only (tooling, docker, scripts, project scaffolding), and must say when it does.
- When I'm stuck: hint first, then a small snippet, full solution only if I explicitly ask.
- Explain new concepts by mapping from TypeScript/React/Node first (Promise -> Task, map/filter -> LINQ, etc.).
- Every lesson follows the roadmap loop: LEARN (theory) -> BUILD (my code) -> DEBUG (break it once) -> CHECK (checkpoint + interview questions).
- Code review: point out bugs, non-idiomatic C#, and anything an interviewer would ask about. Be direct.
- Follow the roadmap order and its "keep it simple" rule: layered monolith, no CQRS/MediatR/microservices/extra projects.
- Lessons go in `docs/lessons/NN-topic.md` (Claude writes these), my own notes in `docs/notes/`.
- After each topic: update `docs/progress.md` and add the topic's questions to `docs/interview-questions.md`.

## Where I am now
See `docs/progress.md` (the "Current topic" line at the top is the source of truth).

## Environment
- Local machine: macOS. Editor: Rider or VS Code + C# Dev Kit. DB: SQL Server in Docker (`docker compose up -d`).
  SSMS is Windows-only -> use VS Code "SQL Server (mssql)" extension or DBeaver.
- Debugging labs (breakpoints, Watch, Call Stack) are done locally: the cloud session has no visual debugger.
- Cloud sessions (claude.ai/code): `scripts/cloud-setup.sh` runs on session start (installs .NET 10, starts SQL Server).

## Commands
- Build: `dotnet build`
- Run API: `dotnet run --project src/ProjectHub.Api` (OpenAPI doc at `/openapi/v1.json` in Development)
- Tests (from week 3): `dotnet test`
- SQL Server: `docker compose up -d` -> `localhost,1433`, user `sa`, password from `docker-compose.yml` (dev only)

## Stack
.NET 10 / C# 14, ASP.NET Core controllers, EF Core + SQL Server 2025, xUnit, React + TypeScript (Vite) later.
