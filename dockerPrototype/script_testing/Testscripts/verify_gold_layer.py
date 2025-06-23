from pyspark.sql import SparkSession
import os

def main():
    """
    Dieses Skript liest die Tabellen aus der Gold-Schicht
    und zeigt die ersten 5 Zeilen jeder Tabelle an.
    """
    spark = SparkSession.builder \
        .appName("GoldSchichtVerifizierer") \
        .getOrCreate()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    gold_data_path = os.path.join(base_dir, "..", "data", "gold")
    
    print(f"Lese Gold-Tabellen aus: {gold_data_path}\n")

    tabellen = ["dim_modul", "dim_zeit", "dim_messung", "faktentabelle"]

    for tabelle in tabellen:
        print("==============================================")
        print(f"   Tabelle: {tabelle.upper()}")
        print("==============================================")
        
        tabelle_pfad = os.path.join(gold_data_path, tabelle)
        
        try:
            df = spark.read.parquet(tabelle_pfad)
            
            print("Schema:")
            df.printSchema()
            
            print("\nErste 5 Zeilen:")
            df.show(10, truncate=False)
            
        except Exception as e:
            print(f"Fehler beim Lesen der Tabelle {tabelle} aus {tabelle_pfad}: {e}")
        
        print("\n")

    spark.stop()
    print("Verifizierung abgeschlossen.")

if __name__ == '__main__':
    main()