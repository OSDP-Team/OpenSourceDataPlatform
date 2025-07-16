import os
import io
import random
from datetime import datetime, timedelta
from minio import Minio

MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BRONZE_BUCKET = "bronze"

SIMULATION_DATE_STR = "2023-01-02"

MODULES_TO_SIMULATE = [
    {"name": "Strom_GOM_M1", "interval": "15_min"},
    {"name": "Strom_GOM_M2", "interval": "15_min"},
    {"name": "Nutzungsgrad_GOM_M3_el", "interval": "Täglich"},
]

def generate_csv_data(module_name, start_timestamp, num_rows, interval_minutes):
    """Erzeugt CSV-Daten als String im Arbeitsspeicher."""
    output = io.StringIO()
    header = "COMP_LEVEL;VALUEDATE;MESS_ID;VALUE;STATE_VAL;STATE_ACQ;STATE_COR;ENTRYDATE;MIN;MINDATE;MAX;MAXDATE;AVG;SUM;PVALUE;OFFSET;VERSION;TEXT\n"
    output.write(header)

    current_timestamp = start_timestamp
    for _ in range(num_rows):
        valuedate_str = current_timestamp.strftime('%d.%m.%Y %H:%M:%S')
        
        base_value = random.uniform(0.0, 0.2)

        min_val = base_value * random.uniform(0.9, 0.98)
        max_val = base_value * random.uniform(1.02, 1.1)
        avg_val = (min_val + max_val) / 2
        sum_val = avg_val * 4

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
    
    return output.getvalue().encode('utf-8')

if __name__ == "__main__":
    print("Starte Daten-Generator (einmalige Ausführung)...")
    
    try:
        simulation_date = datetime.strptime(SIMULATION_DATE_STR, "%Y-%m-%d")
    except ValueError:
        print(f"FEHLER: Ungültiges Datumsformat in SIMULATION_DATE_STR. Bitte YYYY-MM-DD verwenden.")
        exit()
    
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

    print(f"\n[{simulation_date.strftime('%Y-%m-%d %H:%M:%S')}] Generiere eine neue Daten-Charge...")

    for module in MODULES_TO_SIMULATE:
        filename = f"messwerte_{simulation_date.strftime('%Y%m%d_%H%M%S')}_{module['name']}.csv"
        object_name = f"modul={module['name']}/intervall={module['interval']}/{filename}"
        
        data = None
        if module["interval"] == "15_min":
            timestamp_to_generate = simulation_date - timedelta(minutes=15)
            data = generate_csv_data(module['name'], timestamp_to_generate, 96, 15)
            print(f"  -> Generiere 15-Minuten-Daten für Modul '{module['name']}'...")
            
        elif module["interval"] == "Täglich":
            yesterday = simulation_date - timedelta(days=1)
            start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
            data = generate_csv_data(module['name'], start_of_yesterday, 96, 1440)
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
