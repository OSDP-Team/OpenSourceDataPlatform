FROM python:3.10

# Systemtools installieren (optional)
RUN apt-get update && apt-get install -y git

# Arbeitsverzeichnis
WORKDIR /app

# Lokale Dateien ins Image kopieren (werden vom Workflow bereitgestellt)
COPY . /app

# Optional: Abhängigkeiten installieren
# RUN pip install -r requirements.txt

# Standardverhalten
CMD ["sleep", "infinity"]
