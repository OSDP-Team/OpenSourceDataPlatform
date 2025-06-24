from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, year, month, dayofmonth
from pyspark.sql.types import IntegerType, DoubleType
import os

def main():
    """
    Hauptfunktion zur Ausführung des Spark-Jobs.
    """
    #with open("/minio-s3-credentials/accessKey", "r") as f:
    #    minio_user = f.read().strip()

    #with open("/minio-s3-credentials/secretKey", "r") as f:
   #     minio_pwd = f.read().strip()

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

    bronze_bucket = "bronze"
    silver_bucket = "silver/data"
    
    bronze_data_path = f"s3a://{bronze_bucket}"
    silver_data_path = f"s3a://{silver_bucket}"

    print(bronze_data_path)
    print(silver_data_path)
    
    print(f"Lese Daten aus dem Bronze-Verzeichnis: {bronze_data_path}")
    print(f"Schreibe verarbeitete Daten in das Silber-Verzeichnis: {silver_data_path}")

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
        transformed_df = bronze_df.select(
            col("modul"),
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

    cleaned_df = transformed_df.na.drop(subset=["mess_id", "comp_level", "valuedate"])
    
    cleaned_df = cleaned_df.filter((col("value") > 0) & (col("pvalue") > 0))
    
    print("Verarbeitete Daten. Neues Schema:")
    cleaned_df.printSchema()
    print("Beispieldaten aus der Silber-Schicht (erste 5 Zeilen):")
    cleaned_df.show(5)

    print("Füge Partitionierungsspalten (year, month) hinzu.")
    
    partitioned_df = cleaned_df.withColumn("year", year(col("valuedate"))) \
        .withColumn("month", month(col("valuedate")))
    
    try:
        print(f"Schreibe Daten nach {silver_data_path}, partitioniert nach mess_id, year, month.")
    
        partitioned_df \
            .write \
            .mode("overwrite") \
            .partitionBy("modul", "mess_id", "year", "month") \
            .parquet(silver_data_path)
        
        print("Daten erfolgreich geschrieben.")

    except Exception as e:
        print(f"Fehler beim Schreiben der Daten: {e}")


    spark.stop()
    print("Spark Session beendet.")

if __name__ == '__main__':
    main()
