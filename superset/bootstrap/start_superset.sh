#!/bin/sh
set -eu

log() {
  echo "[superset-start] $*"
}

log "Starting Superset database migration"
superset db upgrade

log "Creating Superset admin user if needed"
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME}" \
  --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
  --lastname "${SUPERSET_ADMIN_LASTNAME}" \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" \
  || log "Superset admin user may already exist"

log "Initializing Superset permissions and roles"
superset init

log "Bootstrapping Smart DW database, datasets, charts, and dashboard"
python /app/bootstrap/bootstrap_superset.py

log "Starting Superset web server on 0.0.0.0:8088"
exec superset run -h 0.0.0.0 -p 8088
