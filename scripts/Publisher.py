# data_generator.py (Angepasst für die einmalige Ausführung durch einen Orchestrator)
import os
import io
import random
from datetime import datetime, timedelta
from minio import Minio

# --- KONFIGURATION ---
MINIO_ENDPOINT = "localhost:9000"  
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BRONZE_BUCKET = "bronze"

MODULES_TO_SIMULATE = [
    {"name": "Strom_GOM_M1", "interval": "15_min"},
    {"name": "Strom_GOM_M2", "interval": "15_min"},
    {"name": "Nutzungsgrad_M3", "interval": "täglich"},
    {"name": "Waerme_GOM_M2", "interval": "15_min"},
]

# --- HILFSFUNKTIONEN ---

def generate_csv_data(start_timestamp, num_rows, interval_minutes):
    """Erzeugt CSV-Daten als String im Arbeitsspeicher."""
    output = io.StringIO()
    # CSV-Header schreiben
    header = "COMP_LEVEL;VALUEDATE;MESS_ID;VALUE;STATE_VAL;STATE_ACQ;STATE_COR;ENTRYDATE;MIN;MINDATE;MAX;MAXDATE;AVG;SUM;PVALUE;OFFSET;VERSION;TEXT\n"
    output.write(header)

    current_timestamp = start_timestamp
    for _ in range(num_rows):
        # Zeitstempel für die aktuelle Zeile
        valuedate_str = current_timestamp.strftime('%d.%m.%Y %H:%M:%S')
        
        # Realistische, zufällige Messwerte generieren
        base_value = random.uniform(50.0, 200.0)
        if "Nutzungsgrad" in start_timestamp.strftime("%Y-%m-%d"): # Simple way to check module type for value generation
            base_value = random.uniform(0.85, 0.99)

        min_val = base_value * random.uniform(0.9, 0.98)
        max_val = base_value * random.uniform(1.02, 1.1)
        avg_val = (min_val + max_val) / 2
        sum_val = avg_val * 4 # Annahme für 15-Min-Summen

        # Eine CSV-Zeile formatieren
        row = [
            "2100", valuedate_str, str(random.randint(180000, 190000)),
            f"{base_value:.6f}", "50", "0", "0",
            datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            f"{min_val:.6f}", valuedate_str, f"{max_val:.6f}", valuedate_str,
            f"{avg_val:.6f}", f"{sum_val:.6f}", f"{base_value * 4:.6f}",
            "1", "01.01.0001 00:00:00", ""
        ]
        output.write(";".join(row) + "\n")
        
        current_timestamp += timedelta(minutes=interval_minutes)
    
    # Den Inhalt als Bytes zurückgeben, bereit für den Upload
    return output.getvalue().encode('utf-8')


# --- HAUPTSKRIPT ---

if __name__ == "__main__":
    print("Starte Daten-Generator (einmalige Ausführung)...")
    
    # MinIO Client initialisieren
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        found = minio_client.bucket_exists(BRONZE_BUCKET)
        if not found:
            minio_client.make_bucket(BRONZE_BUCKET)
            print(f"Bucket '{BRONZE_BUCKET}' wurde erstellt.")
    except Exception as e:
        print(f"Fehler bei der Verbindung zu MinIO: {e}")
        exit()

    now = datetime.now()
    print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Generiere eine neue Daten-Charge...")

    for module in MODULES_TO_SIMULATE:
        # Eindeutigen Dateinamen erstellen
        filename = f"messwerte_{now.strftime('%Y%m%d_%H%M%S')}_{module['name']}.csv"
        
        # Korrekten Objektpfad für die Partitionierung zusammenbauen
        object_name = f"modul={module['name']}/intervall={module['interval']}/{filename}"
        
        data = None
        # Logik, um zu entscheiden, welche Daten generiert werden sollen
        if module["interval"] == "15_min":
            # Generiere Daten für das letzte abgeschlossene 15-Minuten-Intervall
            timestamp_to_generate = now - timedelta(minutes=15)
            data = generate_csv_data(timestamp_to_generate, 1, 15)
            print(f"  -> Generiere 15-Minuten-Daten für Modul '{module['name']}'...")
            
        elif module["interval"] == "täglich":
            # Generiere Daten für den gesamten gestrigen Tag
            yesterday = now - timedelta(days=1)
            start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
            # 96 Intervalle à 15 Minuten = 24 Stunden
            data = generate_csv_data(start_of_yesterday, 96, 15)
            print(f"  -> Generiere Tages-Daten für Modul '{module['name']}' für den {start_of_yesterday.date()}...")

        if data:
            data_stream = io.BytesIO(data)
            data_len = len(data)

            try:
                minio_client.put_object(
                    BRONZE_BUCKET,
                    object_name,
                    data_stream,
                    data_len,
                    content_type='application/csv'
                )
                print(f"  -> SUCCESS: '{filename}' erfolgreich hochgeladen.")
            except Exception as e:
                print(f"  -> ERROR: Fehler beim Upload für Modul '{module['name']}': {e}")
    
    print("\nDaten-Generierung abgeschlossen. Skript wird beendet.")
