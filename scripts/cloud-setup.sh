#!/usr/bin/env bash
# Runs on session start in Claude Code cloud sessions only (the container is fresh each time).
# Installs the .NET 10 SDK and starts SQL Server in Docker. Locally on the Mac this does nothing.
set -uo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "$(dirname "$0")/.."

if ! command -v dotnet >/dev/null 2>&1; then
  (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dotnet-sdk-10.0) >/dev/null 2>&1
fi

if ! docker info >/dev/null 2>&1; then
  (dockerd >/tmp/dockerd.log 2>&1 &)
  for _ in $(seq 1 20); do docker info >/dev/null 2>&1 && break; sleep 1; done
fi

# Pulling the image takes a while, so don't block session start on it.
nohup docker compose up -d >/tmp/sqlserver-up.log 2>&1 &

dotnet restore >/dev/null 2>&1 || true
dotnet tool restore >/dev/null 2>&1 || true   # dotnet-ef (Topic 10)
echo "cloud-setup: dotnet $(dotnet --version 2>/dev/null || echo missing); SQL Server starting (see /tmp/sqlserver-up.log)"
