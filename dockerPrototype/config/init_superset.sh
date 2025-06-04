#!/bin/bash

# Konfiguriert Superset automatisch
superset db upgrade
superset fab create-admin \
  --username "$SUPERSET_USER" \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password "$SUPERSET_PASSWORD"
superset init

superset set-database-uri \
  --database-name analyse-db \
  --uri "$SUPERSET_DATABASE_URL"

# Command einbinden um Yamls automatisch zu importieren
# superset import-assets --path /app/config/assets

# Starte Superset
superset run -h 0.0.0.0 -p 8088