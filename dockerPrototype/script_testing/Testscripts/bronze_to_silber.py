from pyspark.sql import SparkSession
from pyspark.sql.functions import split #ÄNDERUNG
from pyspark.sql.functions import col, to_timestamp, year, month, dayofmonth
from pyspark.sql.types import IntegerType, DoubleType
import os

def main():
    """
    Hauptfunktion zur Ausführung des Spark-Jobs.
    """
    spark = SparkSession.builder \
        .appName("BronzeZuSilberProzessor") \
        .getOrCreate()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    bronze_data_path = os.path.join(base_dir, "..", "data", "bronze")
    silver_data_path = os.path.join(base_dir, "..", "data", "silver")
    
    print(f"Lese Daten aus dem Bronze-Verzeichnis: {bronze_data_path}")
    print(f"Schreibe verarbeitete Daten in das Silber-Verzeichnis: {silver_data_path}")

    os.makedirs(silver_data_path, exist_ok=True)

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

    try:
        base_transformed_df = bronze_df.select( #ÄNDERUNG
            col("modul"),
            col("intervall"), #ÄNDERUNG
            col("COMP_LEVEL").alias("comp_level").cast(IntegerType()),
            to_timestamp(col("VALUEDATE"), "dd.MM.yyyy HH:mm:ss").alias("valuedate"),
            col("MESS_ID").alias("mess_id").cast(IntegerType()),
            col("VALUE").alias("value").cast(DoubleType()),  
            col("STATE_VAL").alias("state_val").cast(IntegerType()),
            col("STATE_ACQ").alias("state_acq").cast(IntegerType()),
            col("STATE_COR").alias("state_cor").cast(IntegerType()),
            to_timestamp(col("ENTRYDATE"), "dd.MM.yyyy HH:mm:ss").alias("entrydate"),
            col("MIN").alias("min").cast(DoubleType()),
            to_timestamp(col("MINDATE"), "dd.MM.yyyy HH:mm:ss").alias("mindate"),
            col("MAX").alias("max").cast(DoubleType()),
            to_timestamp(col("MAXDATE"), "dd.MM.yyyy HH:mm:ss").alias("maxdate"),
            col("AVG").alias("avg").cast(DoubleType()),
            col("SUM").alias("sum").cast(DoubleType()),
            col("PVALUE").alias("pvalue").cast(DoubleType()),
            col("OFFSET").alias("offset").cast(IntegerType()),
            col("VERSION").alias("version"),
            col("TEXT").alias("text") 
    )
    except Exception as e:
        print(f"Ein Fehler ist bei der Transformation aufgetreten: {e}")
        spark.stop()
        return

    #<----------- START DER ÄNDERUNG ------------>
    try:
        transformed_df = base_transformed_df.withColumn(
            "messung_typ",
            split(col("modul"), "_").getItem(0)
        )
    except Exception as e:
        print(f"Ein Fehler ist bei der Transformation der Messtypen aufgetreten : {e}")
        spark.stop()
        return
    
    print("\nStarte Datenbereinigung...")
    transformed_df.cache()
    
    count_initial = transformed_df.count()
    print(f"Anzahl Zeilen vor der Bereinigung: {count_initial}")
    
    df_after_drop = transformed_df.na.drop(subset=["mess_id", "comp_level", "valuedate"])
    count_after_drop = df_after_drop.count()
    
    dropped_by_na = count_initial - count_after_drop
    if dropped_by_na > 0:
        print(f"--> {dropped_by_na} Zeilen wurden wegen NULL-Werten entfernt.")

    cleaned_df = df_after_drop.filter((col("value") > 0) & (col("pvalue") > 0))
    count_after_filter = cleaned_df.count()

    dropped_by_filter = count_after_drop - count_after_filter
    if dropped_by_filter > 0:
        print(f"--> {dropped_by_filter} Zeilen wurden wegen ungültiger Messwerte (<= 0) entfernt.")

    print(f"Anzahl Zeilen nach der Bereinigung: {count_after_filter}\n")

    transformed_df.unpersist()
    #<------------ ENDE DER ÄNDERUNG --------------->
    print("Verarbeitete Daten. Neues Schema:")
    cleaned_df.printSchema()
    print("Beispieldaten aus der Silber-Schicht (erste 5 Zeilen):")
    cleaned_df.show(5)

    print("Füge Partitionierungsspalten (year, month) hinzu.")
    
    partitioned_df = cleaned_df.withColumn("year", year(col("valuedate"))) \
        .withColumn("month", month(col("valuedate")))
    
    try:
        print(f"Schreibe Daten nach {silver_data_path}, partitioniert nach modul, intervall, mess_id, year, month.") #ÄNDERUNG
        #ÄNDERUNG
        partitioned_df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .partitionBy("modul", "intervall", "mess_id", "year", "month") \
            .parquet(silver_data_path)
        
        print("Daten erfolgreich geschrieben.")

    except Exception as e:
        print(f"Fehler beim Schreiben der Daten: {e}")


    spark.stop()
    print("Spark Session beendet.")

if __name__ == '__main__':
    main()
