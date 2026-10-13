# ProjectHub: learning C#/.NET backend (and fullstack)

## Who I am and why this repo exists
- Experienced React + TypeScript frontend developer moving to fullstack at my company (backend is C#/.NET).
- My teamlead gave me a roadmap: "React/TypeScript -> C#/.NET Backend" (4-week track, 2-3 h/day).
  The topic list and checkpoints are in `docs/progress.md`.
- After the roadmap my teamlead will interview me on it, and only then let me into our real (complex) backend.
- Final goals: (1) pass the interview on everything in the readiness checklist, (2) a finished fullstack app:
  ProjectHub API (ASP.NET Core + EF Core + SQL Server) + React/TypeScript frontend in `web/`.

## How Claude must work in this repo: REVIEWER MODE (changed from tutor mode)
- **Claude writes the code; I read, review, question and challenge it.** At work we use AI for coding, so the goal is to
  *understand* (concepts, patterns, how it all fits, DB, HTTP, EF) and be able to explain and defend every line, not to type it.
- Every piece of code comes with a **deep explanation**: what it does, why this design, trade-offs, what an interviewer would ask.
- Explain new concepts by mapping from TypeScript/React/Node first (Promise -> Task, map/filter -> LINQ, etc.).
- After each piece, quiz me on it (short questions). I must be able to answer without notes. Correct me directly when I'm wrong.
- Every lesson follows the roadmap loop: LEARN (theory) -> BUILD (Claude writes, I review and ask) -> DEBUG (break it once, I drive the debugger locally) -> CHECK (checkpoint + interview questions).
- Follow the roadmap order and its "keep it simple" rule: layered monolith, no CQRS/MediatR/microservices/extra projects.
- Lessons go in `docs/lessons/NN-topic.md` (Claude writes these), my own notes in `docs/notes/`.
- After each topic: update `docs/progress.md` and add the topic's questions to `docs/interview-questions.md`.
- **Every topic ends with a study book PDF** in `docs/studybooks/NN-topic.pdf` (generator script in `scripts/studybooks/`).
  Thorough, not a cheat sheet: brief overview at the start, then everything covered in the topic (theory, our code explained,
  experiments, debugging steps, the questions I asked and the answers, mistakes I made and corrections, interview Q&A with
  model answers), and a summary at the end.
- The final ticket (topic 20) is still done by me with docs only: that is the independence check.

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
