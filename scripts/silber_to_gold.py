from pyspark.sql import SparkSession
from pyspark.sql.functions import when
from pyspark.sql.functions import col, monotonically_increasing_id, to_date, year, month, dayofmonth, hour, minute

def main():
    """
    Hauptfunktion zur Ausführung des Spark-Jobs.
    """
    #with open("/minio-s3-credentials/accessKey", "r") as f:
     #   minio_user = f.read().strip()

    #with open("/minio-s3-credentials/secretKey", "r") as f:
     #   minio_pwd = f.read().strip()

    minio_user = os.getenv("MINIO_ACCESS_KEY")
    minio_pwd = os.getenv("MINIO_SECRET_KEY")

    print(f"MINIO_ACCESS_KEY: {minio_user}")
    print(f"MINIO_SECRET_KEY: {minio_pwd}")

    if not minio_user or not minio_pwd:
        raise ValueError("MINIO_ACCESS_KEY oder MINIO_SECRET_KEY nicht gesetzt")
    
    spark = (
    SparkSession.builder
        .appName("local-with-s3a")
        .master("local[*]")

        .config(
            "spark.jars.packages",
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.688"
        )

        .config("spark.hadoop.fs.s3a.impl",
                "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.access.key",  minio_user) \
        .config("spark.hadoop.fs.s3a.secret.key",  minio_pwd) \

        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
        .config("spark.hadoop.fs.s3a.committer.name", "directory") \
        .getOrCreate()
    )

    silver_bucket = "silver"
    gold_bucket = "gold/data"
    
    gold_data_path = f"s3a://{gold_bucket}"
    silver_data_path = f"s3a://{silver_bucket}"
    
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

    print("Erstelle DIM Zeit...")
    dim_zeit_df = silver_df.select("valuedate", "intervall").distinct() \
        .withColumn("zeit_Id", monotonically_increasing_id()) \
        .withColumn("datum", to_date(col("valuedate"))) \
        .withColumn("jahr", year(col("valuedate"))) \
        .withColumn("monat", month(col("valuedate"))) \
        .withColumn("tag", dayofmonth(col("valuedate"))) \
        .withColumn("stunde", hour(col("valuedate"))) \
        .withColumn("minute", minute(col("valuedate"))) 
    
    dim_zeit_df = dim_zeit_df.select("zeit_Id", "datum", "jahr", "monat", "tag", "stunde", "minute", "intervall", "valuedate")

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

if __name__ == '__main__':
    from pyspark.sql.functions import lit
    import os
    main()