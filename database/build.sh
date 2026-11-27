#!/usr/bin/env bash
# Build the RescueVision database from scratch.
#
#   ./database/build.sh                 # schema + reference data + demo scenario
#   ./database/build.sh --no-demo       # schema + reference data only
#   DB_NAME=rescuevision_test ./database/build.sh # another database name
#
# Connection uses the standard libpq variables (PGHOST, PGPORT, PGUSER, PGPASSWORD).
# WARNING: drops and recreates $DB_NAME.
set -euo pipefail

DB_NAME="${DB_NAME:-rescuevision}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_DEMO=1
[[ "${1:-}" == "--no-demo" ]] && WITH_DEMO=0

PSQL=(psql -v ON_ERROR_STOP=1 -X -q)

echo "→ Recreating database '$DB_NAME'"
"${PSQL[@]}" -d postgres -c "DROP DATABASE IF EXISTS \"$DB_NAME\" WITH (FORCE);"
"${PSQL[@]}" -d postgres -c "CREATE DATABASE \"$DB_NAME\";"

for f in "$HERE"/schema/*.sql; do
  echo "→ schema  $(basename "$f")"
  "${PSQL[@]}" -d "$DB_NAME" -f "$f"
done

echo "→ seed    01_reference_data.sql"
"${PSQL[@]}" -d "$DB_NAME" -f "$HERE/seed/01_reference_data.sql"

if [[ $WITH_DEMO -eq 1 ]]; then
  echo "→ seed    02_demo_scenario.sql"
  "${PSQL[@]}" -d "$DB_NAME" -f "$HERE/seed/02_demo_scenario.sql"
fi

echo "→ tests   checks.sql"
"${PSQL[@]}" -d "$DB_NAME" -f "$HERE/tests/checks.sql"

TABLES=$("${PSQL[@]}" -At -d "$DB_NAME" -c "
  SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND NOT c.relispartition
    AND c.relname <> 'spatial_ref_sys';")
echo "✓ '$DB_NAME' ready: $TABLES tables"
