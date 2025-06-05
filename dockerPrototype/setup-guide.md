# OSDP Setup Guide

Dieses Dokument beschreibt die Einrichtung der lokalen Entwicklungsumgebung für das OSDP-Projekt mit Docker, PostgreSQL und PySpark/Superset-Anbindung.

---

## Voraussetzungen

- Docker Desktop installiert ([Download](https://www.docker.com/products/docker-desktop))
- `docker compose` verfügbar (ab Docker Desktop v2 enthalten)
- `.env`-Datei mit Konfiguration vorhanden (nicht im Git-Repo!)

---

## .env-Datei 

Erstelle im Verzeichnis `docker/` eine Datei namens `.env`.

'.env.example' zeigt dabei wie diese Datei aussehen kann.

---

## Start der PostgreSQL-Datenbank und Superset

Wechsle ins Docker-Verzeichnis:

```bash
cd docker
docker compose up -d
```

Der Container heißt `analyse-db` und ist auf Port `5432` verfügbar.

---

## Verbindung zur Datenbank testen

```bash
docker exec -it analyse-db psql -U user -d analyse
```

Wenn du die psql-Shell siehst (`analyse=#`), ist die Verbindung erfolgreich.

---

## Verwendung von Python

Für die Verarbeitung der CSV-Datei mit PySpark wird eine Python-Umgebung empfohlen.

### Schritte zur Einrichtung:

1. Erstelle eine virtuelle Umgebung im Hauptverzeichnis:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Installiere die benötigten Pakete:

   ```bash
   pip install -r requirements.txt
   ```

3. Starte das Skript:

   ```bash
   python scripts/transform.py
   ```

Die Daten werden aus der Datei `data/Data.csv` gelesen und in die PostgreSQL-Datenbank geschrieben.  
Erfolgreiche Durchläufe werden in der Datei `output/log.txt` dokumentiert.

---

## Superset verwenden

Nach dem Start mit `docker compose up -d` ist Superset im Browser erreichbar unter:

http://localhost:8088

Melde dich mit folgenden Standarddaten an:

- Benutzername: `admin`
- Passwort: `admin`

**Hinweis:** Dieses Superset-Setup ist nicht für Produktionsumgebungen gedacht.  
Für Produktivbetrieb siehe: https://superset.apache.org/docs/installation/installing-superset-using-kubernetes

## Hinweise

- Volumes sorgen für persistente Daten: `pgdata:/var/lib/postgresql/data`
- Löschen aller Daten: `docker compose down -v`
- `.env` wird automatisch geladen – keine Passwörter in `docker-compose.yml`
- Zum stoppen des Containers:

```bash
cd docker
docker compose stop
```

- Superset wird hier mit Docker Compose betrieben, was **nicht für Produktivbetrieb empfohlen** wird. Für produktive Nutzung siehe die offizielle Superset-Dokumentation zur Kubernetes-Installation.

---

## Kurzinstallation

```bash
chmod +x scripts/init_project.sh
./scripts/init_project.sh
```

**Achtung:** Das Setup-Skript ist nicht getestet und aktuell nicht zu empfehlen