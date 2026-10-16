#!/usr/bin/env bash
# Run one or more .sql files against the local SQL Server container (docker compose up -d first).
# Uses sqlcmd INSIDE the container, so nothing needs to be installed on the Mac.
# Usage (from the repo root):  ./scripts/run-sql.sh sql/01-create-database.sql sql/02-create-tables.sql sql/03-seed-data.sql
set -euo pipefail

PASSWORD="${MSSQL_SA_PASSWORD:-ProjectHub_Dev123!}"

for file in "$@"; do
  echo "=== $file"
  docker exec -i projecthub-sql /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "$PASSWORD" -C -b -W < "$file"
done
