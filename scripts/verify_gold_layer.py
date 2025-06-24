from pyspark.sql import SparkSession
import os

def main():
    """
    Dieses Skript liest die Tabellen aus der Gold-Schicht
    und zeigt die ersten 5 Zeilen jeder Tabelle an.
    """
    with open("/minio-s3-credentials/accessKey", "r") as f:
        minio_user = f.read().strip()

    with open("/minio-s3-credentials/secretKey", "r") as f:
        minio_pwd = f.read().strip()
    
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

    gold_bucket = "gold"
    
    gold_data_path = f"s3a://{gold_bucket}"
    
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