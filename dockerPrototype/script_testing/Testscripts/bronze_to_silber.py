from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, year, month, dayofmonth
from pyspark.sql.types import IntegerType, DoubleType
import os

def main():
    """
    Hauptfunktion zur Ausführung des Spark-Jobs.
    """
    # 1. Spark Session initialisieren
    # Die Konfiguration für den PostgreSQL-Treiber wird entfernt, da sie nicht mehr benötigt wird.
    spark = SparkSession.builder \
        .appName("BronzeZuSilberProzessor") \
        .getOrCreate()

    # Pfade definieren
    # Annahme: Das Skript wird in einem 'scripts'-Ordner ausgeführt.
    # Die Daten liegen in einem übergeordneten 'data'-Ordner.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bronze_data_path = os.path.join(base_dir, "..", "data", "bronze")
    silver_data_path = os.path.join(base_dir, "..", "data", "silver")
    
    print(f"Lese Daten aus dem Bronze-Verzeichnis: {bronze_data_path}")
    print(f"Schreibe verarbeitete Daten in das Silber-Verzeichnis: {silver_data_path}")

    # Sicherstellen, dass die Ausgabeverzeichnisse existieren
    os.makedirs(silver_data_path, exist_ok=True)

    # 2. Daten aus dem Bronze-Ordner lesen
    # Spark kann alle CSVs in einem Verzeichnis auf einmal einlesen.
    # Das Schema wird automatisch erkannt (inferSchema=True).
    try:
        bronze_df = spark.read \
            .option("header", True) \
            .option("sep", ";") \
            .option("inferSchema", True) \
            .csv(bronze_data_path)
    except Exception as e:
        print(f"Fehler beim Lesen der Daten aus {bronze_data_path}: {e}")
        spark.stop()
        return

    print("Daten erfolgreich geladen. Ursprüngliches Schema:")
    bronze_df.printSchema()
    print("Beispieldaten aus der Bronze-Schicht (erste 5 Zeilen):")
    bronze_df.show(5)

    # 3. Typische "Bronze zu Silber" Transformationen
    
    # 3.1 Spalten umbenennen für bessere Lesbarkeit und Konsistenz
    # Beispiel: Entfernen von Leerzeichen oder Sonderzeichen
    transformed_df = bronze_df \
        .withColumnRenamed("COMP_LEVEL", "comp_level") \
        .withColumnRenamed("VALUEDATE", "valuedate") \
        .withColumnRenamed("MESS_ID", "mess_id") \
        .withColumnRenamed("VALUE", "value") \
        .withColumnRenamed("STATE_VAL", "state_val") \
        .withColumnRenamed("STATE_ACQ", "state_acq") \
        .withColumnRenamed("STATE_COR", "state_cor") \
        .withColumnRenamed("ENTRYDATE", "entrydate") \
        .withColumnRenamed("MIN", "min") \
        .withColumnRenamed("MINDATE", "mindate") \
        .withColumnRenamed("MAX", "max") \
        .withColumnRenamed("MAXDATE", "maxdate") \
        .withColumnRenamed("AVG", "avg") \
        .withColumnRenamed("SUM", "sum") \
        .withColumnRenamed("PVALUE", "pvalue") \
        .withColumnRenamed("OFFSET", "offset") \
        .withColumnRenamed("VERSION", "version") \
        .withColumnRenamed("TEXT", "text") 

    # 3.2 Datentypen korrigieren (Type Casting)
    # Oft werden Zahlen als Strings eingelesen. Wir konvertieren sie hier.
    # Datumsangaben werden in ein echtes Timestamp-Format umgewandelt.
    transformed_df = transformed_df \
        .withColumn("com_level", col("comp_level").cast(IntegerType())) \
        .withColumn("valuedate", to_timestamp(col("valuedate"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("mess_id", col("mess_id").cast(IntegerType())) \
        .withColumn("value", col("value").cast(DoubleType)) \
        .withColumn("state_val", col("state_val").cast(IntegerType)) \
        .withColumn("state_acq", col("state_acq").cast(IntegerType)) \
        .withColumn("state_cor", col("state_cor").cast(IntegerType)) \
        .withColumn("entrydate", to_timestamp(col("entrydate"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("min", col("min").cast(DoubleType)) \
        .withColumn("mindate", to_timestamp(col("mindate"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("max", col("max").cast(DoubleType)) \
        .withColumn("maxdate", to_timestamp(col("maxdate"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("avg", col("avg").cast(DoubleType)) \
        .withColumn("sum", col("sum").cast(DoubleType)) \
        .withColumn("pvalue", col("pvalue").cast(DoubleType)) \
        .withColumn("offset", col("offset").cast(IntegerType)) \
        .withColumn("version", to_timestamp(col("version"), "yyyy-MM-dd HH:mm:ss")) \

    # 3.3 Umgang mit fehlenden oder fehlerhaften Werten
    # Wir entfernen alle Zeilen, bei denen eine wichtige Information fehlt.
    cleaned_df = transformed_df.na.drop(subset=["mess_id", "comp_level"])
    
    # Filtern von ungültigen Daten
    cleaned_df = cleaned_df.filter((col("value") > 0) & (col("pvalue") > 0))
    
    print("Verarbeitete Daten. Neues Schema:")
    cleaned_df.printSchema()
    print("Beispieldaten aus der Silber-Schicht (erste 5 Zeilen):")
    cleaned_df.show(5)

    # 4. Verarbeiteten DataFrame in den Silber-Ordner schreiben
    # Parquet ist ein spaltenorientiertes Format, das für analytische Abfragen optimiert ist.
    # Es bietet Kompression und speichert das Schema mit den Daten.
    try:
        cleaned_df.write \
            .mode("overwrite") \
            .partitionBy("valuedate", "version") \
            .parquet(silver_data_path)
        print(f"Daten erfolgreich nach {silver_data_path} geschrieben und partitioniert.")
    except Exception as e:
        print(f"Fehler beim Schreiben der Daten: {e}")


    # 5. Spark Session beenden
    spark.stop()
    print("Spark Session beendet.")

if __name__ == '__main__':
    main()
