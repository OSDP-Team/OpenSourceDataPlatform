import os
import random
from datetime import datetime, timedelta

LOCAL_OUTPUT_DIR = "generated_bronze_data"

MODULES_TO_SIMULATE = [
    {"name": "Strom_GOM_M1", "interval": "15_min"},
    {"name": "Strom_GOM_M2", "interval": "15_min"},
    {"name": "Nutzungsgrad_GOM_M3_el", "interval": "Täglich"},
    {"name": "Waerme_GOM_M2", "interval": "15_min"},
]

def generate_csv_data(module_name, timestamp, is_daily_summary=False):
    """
    Erzeugt CSV-Daten für einen einzelnen Messpunkt.
    Wenn is_daily_summary=True, werden die Werte als Tageszusammenfassung generiert.
    """
    header = "COMP_LEVEL;VALUEDATE;MESS_ID;VALUE;STATE_VAL;STATE_ACQ;STATE_COR;ENTRYDATE;MIN;MINDATE;MAX;MAXDATE;AVG;SUM;PVALUE;OFFSET;VERSION;TEXT\n"
    
    valuedate_str = timestamp.strftime('%d.%m.%Y %H:%M:%S')
    
    base_avg = random.uniform(0.0, 1.0)
    min_val = base_avg * random.uniform(0.6, 0.8)
    max_val = base_avg * random.uniform(1.2, 1.4)
    avg_val = (min_val + max_val) / 2
    sum_val = avg_val * 96 
    value = avg_val

    row = [
        "2100", valuedate_str, str(random.randint(180000, 190000)),
        f"{value:.6f}", "50", "0", "0",
        datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
        f"{min_val:.6f}", valuedate_str, f"{max_val:.6f}", valuedate_str,
        f"{avg_val:.6f}", f"{sum_val:.6f}", f"{value * 4:.6f}",
        "1", "01.01.0001 00:00:00", ""
    ]
    
    return header + ";".join(row) + "\n"

if __name__ == "__main__":
    print("Starte lokalen Daten-Generator (einmalige Ausführung)...")
    
    os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
    
    current = datetime.now()
    now = current.replace(year=current.year - 2)
    print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Generiere eine neue Daten-Charge...")

    for module in MODULES_TO_SIMULATE:
        filename = f"messwerte_{now.strftime('%Y%m%d_%H%M%S')}_{module['name']}.csv"
        
        partition_path = os.path.join(
            LOCAL_OUTPUT_DIR,
            f"modul={module['name']}",
            f"intervall={module['interval']}"
        )
        
        os.makedirs(partition_path, exist_ok=True)
        
        full_file_path = os.path.join(partition_path, filename)

        data_content = None
        if module["interval"] == "15_min":
            timestamp_to_generate = now - timedelta(minutes=15)
            data_content = generate_csv_data(module['name'], timestamp_to_generate, is_daily_summary=False)
            print(f"  -> Generiere 15-Minuten-Daten für Modul '{module['name']}'...")
            
        elif module["interval"] == "Täglich":
            yesterday = now - timedelta(days=1)
            start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
            data_content = generate_csv_data(module['name'], start_of_yesterday, is_daily_summary=True)
            print(f"  -> Generiere Tages-Daten für Modul '{module['name']}' für den {start_of_yesterday.date()}...")

        if data_content:
            try:
                with open(full_file_path, "w", encoding="utf-8") as f:
                    f.write(data_content)
                print(f"  -> SUCCESS: '{filename}' erfolgreich nach '{partition_path}' geschrieben.")
            except Exception as e:
                print(f"  -> ERROR: Fehler beim Schreiben der Datei für Modul '{module['name']}': {e}")
    
    print("\nDaten-Generierung abgeschlossen. Skript wird beendet.")
