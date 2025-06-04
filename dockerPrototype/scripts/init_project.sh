#!/bin/bash

# 0. Setzt virtuelle Umgebung auf, falls nicht vorhanden
if [ ! -d "../.venv" ]; then
  echo "Erstelle virtuelle Python-Umgebung..."
  python3 -m venv ../.venv
  source ../.venv/bin/activate
  pip install --upgrade pip
  pip install -r ../requirements.txt
else
  echo "Aktiviere vorhandene Python-Umgebung..."
  source ../.venv/bin/activate
fi

# 1. Starte Docker-Container (PostgreSQL + Superset)
echo "Starte Docker-Container..."
docker compose -f ../docker/docker-compose.yml up -d --build

# 2. Wartet kurz, bis Container bereit sind
echo "Warte auf Superset..."
sleep 10

# 3. Führt transform.py aus
echo "Führe Datenverarbeitung aus..."
python ./transform.py

# 4. Superset-Initialisierung (läuft containerintern)
echo "Superset wird initialisiert..."

echo "Setup abgeschlossen. Superset läuft unter http://localhost:8088"