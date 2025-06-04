import os

# Superset verwendet diese Datei, wenn sie im Container unter /app/pythonpath/ liegt.

# Stellt sicher, dass Superset dieselbe Datenbank verwendet wie dein Projekt
SQLALCHEMY_DATABASE_URI = os.environ.get("SUPERSET_DATABASE_URL")

# Maximale Anzahl an Ergebnissen pro Abfrage
ROW_LIMIT = 5000

# Längere Timeouts bei langsamen Abfragen
SUPERSET_WEBSERVER_TIMEOUT = 60

# Deaktiviert die Welcome-Tour für neue Benutzer
WELCOME_BANNER_TITLE = ""
WELCOME_BANNER_TEXT = ""