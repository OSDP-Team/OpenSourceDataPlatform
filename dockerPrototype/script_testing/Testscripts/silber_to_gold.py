from pyspark.sql import SparkSession
from pyspark.sql.functions import when #ÄNDERUNG
from pyspark.sql.functions import col, monotonically_increasing_id, to_date, year, month, dayofmonth, hour, minute

def main():
    """
    Hauptfunktion zur Ausführung des Spark-Jobs.
    """
    spark = SparkSession.builder \
        .appName("SilberZuGoldProzessor") \
        .getOrCreate()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    silver_data_path = os.path.join(base_dir, "..", "data", "silver")
    gold_data_path = os.path.join(base_dir, "..", "data", "gold")
    
    print(f"Lese Daten aus der Silber-Schicht: {silver_data_path}")
    print(f"Schreibe Gold-Tabellen nach: {gold_data_path}")

    try:
        silver_df = spark.read.parquet(silver_data_path)
        print("Silber-Daten erfolgreich geladen.")
        silver_df.printSchema()
    except Exception as e:
        print(f"Fehler beim Lesen der Silber-Daten: {e}")
        spark.stop()
        return
    
    print("Erstelle DIM Modul...")
    dim_modul_df = silver_df.select("modul").distinct() \
        .withColumn("modul_Id", monotonically_increasing_id()) \
        .select(col("modul_Id"), col("modul").alias("modul_name"))

    print("Erstelle DIM Zeit...") #ÄNDERUNG
    dim_zeit_df = silver_df.select("valuedate", "intervall").distinct() \
        .withColumn("zeit_Id", monotonically_increasing_id()) \
        .withColumn("datum", to_date(col("valuedate"))) \
        .withColumn("jahr", year(col("valuedate"))) \
        .withColumn("monat", month(col("valuedate"))) \
        .withColumn("tag", dayofmonth(col("valuedate"))) \
        .withColumn("stunde", hour(col("valuedate"))) \
        .withColumn("minute", minute(col("valuedate"))) #ÄNDERUNG
    
    dim_zeit_df = dim_zeit_df.select("zeit_Id", "datum", "jahr", "monat", "tag", "stunde", "minute", "intervall", "valuedate")
    #<----------- START DER ÄNDERUNG --------------->
    print("Erstelle DIM Messung...")
    dim_messung_df = silver_df.select(col("messung_typ").alias("messung_bezeichnung")).distinct() \
    .withColumn("messung_Id", monotonically_increasing_id()) \
    .withColumn(
        "messung_einheit",
        when(col("messung_bezeichnung") == "Nutzungsgrad", "%")
        .otherwise("kWh")
    )
    
    print("Erstelle Faktentabelle durch Verknüpfung mit Dimensionen...")

    faktentabelle_df = silver_df \
        .join(dim_modul_df, silver_df.modul == dim_modul_df.modul_name) \
        .join(dim_zeit_df, silver_df.valuedate == dim_zeit_df.valuedate) \
        .join(dim_messung_df, silver_df.messung_typ == dim_messung_df.messung_bezeichnung) \
        .select(
            col("zeit_Id").alias("FK_zeit_Id"),
            col("modul_Id").alias("FK_modul_Id"),
            col("messung_Id").alias("FK_messung_Id"),
            col("value"),
            col("min"),
            col("max"),
            col("avg"),
            col("sum"),
            col("pvalue")
        )
    #<------------ ENDE DER ÄNDERUNG ---------------->

    print("Speichere Gold-Tabellen (mit je einer Datei pro Tabelle)...")
    try:        
        dim_modul_df.coalesce(1).write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_modul"))
        dim_zeit_df.select("zeit_Id", "datum", "jahr", "monat", "tag", "stunde", "minute", "intervall") \
                   .coalesce(1).write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_zeit"))
                   
        dim_messung_df.coalesce(1).write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_messung"))
        
        faktentabelle_df.coalesce(1).write.mode("overwrite").parquet(os.path.join(gold_data_path, "faktentabelle"))
        
        print("Gold-Schicht erfolgreich erstellt.")
    except Exception as e:
        print(f"Fehler beim Schreiben der Gold-Tabellen: {e}")
    
    # DIESEN CODE FÜR ECHTE UMGEBUNG BENUTZEN!!!!
    """
    print("Speichere Gold-Tabellen...")
    try:
        dim_modul_df.write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_modul"))
        dim_zeit_df.select("zeit_Id", "datum", "jahr", "monat", "tag", "stunde", "minute", "intervall").write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_zeit"))
        dim_messung_df.write.mode("overwrite").parquet(os.path.join(gold_data_path, "dim_messung"))
        faktentabelle_df.write.mode("overwrite").parquet(os.path.join(gold_data_path, "faktentabelle"))
        print("Gold-Schicht erfolgreich erstellt.")
    except Exception as e:
        print(f"Fehler beim Schreiben der Gold-Tabellen: {e}")
    
    spark.stop()
    print("Spark Session beendet.")
    """

if __name__ == '__main__':
    from pyspark.sql.functions import lit
    import os
    main()