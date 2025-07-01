from pyspark.sql import SparkSession
import os

def main():
    """
    Dieses Skript liest die Gold-Tabellen aus MinIO und lädt sie in die
    PostgreSQL-Datenbank.
    """
    #with open("/minio-s3-credentials/accessKey", "r") as f:
     #   minio_access_key = f.read().strip()
    #with open("/minio-s3-credentials/secretKey", "r") as f:
     #   minio_secret_key = f.read().strip()

    minio_user = os.getenv("MINIO_ACCESS_KEY")
    minio_pwd = os.getenv("MINIO_SECRET_KEY")

    print(f"MINIO_ACCESS_KEY: {minio_user}")
    print(f"MINIO_SECRET_KEY: {minio_pwd}")

    if not minio_user or not minio_pwd:
        raise ValueError("MINIO_ACCESS_KEY oder MINIO_SECRET_KEY nicht gesetzt")

    spark = (
        SparkSession.builder
            .appName("GoldZuSupersetPostgres")
            .master("local[*]")
            .config(
                "spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.688,"
                "org.postgresql:postgresql:42.7.3"
            )
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.access.key", minio_user)
            .config("spark.hadoop.fs.s3a.secret.key", minio_pwd)
            .getOrCreate()
    )

    gold_bucket = "gold/data"
    gold_data_path = f"s3a://{gold_bucket}"

    jdbc_hostname = "postgresql-superset"  
    jdbc_port = 5432                       
    jdbc_database = "superset"
    db_schema = "gold_layer"  
    jdbc_url = f"jdbc:postgresql://{jdbc_hostname}:{jdbc_port}/{jdbc_database}"
    
    connection_properties = {
        "user": "superset",
        "password": "superset",
        "driver": "org.postgresql.Driver"
    }

    print(f"Lade Daten aus Gold-Bucket: {gold_data_path}")
    print(f"Schreibe Daten nach PostgreSQL an: {jdbc_url} (Schema: {db_schema})")

    tabellen = ["dim_modul", "dim_zeit", "dim_messung", "faktentabelle"]

    for tabelle_name in tabellen:
        print(f"\nVerarbeite Tabelle: {tabelle_name}...")
        try:
            parquet_pfad = f"{gold_data_path}/{tabelle_name}"
            df = spark.read.parquet(parquet_pfad)
            
            full_table_name = f"{db_schema}.{tabelle_name.lower()}"
            
            df.coalesce(1).write.jdbc( 
                url=jdbc_url,
                table=full_table_name, 
                mode="overwrite",
                properties=connection_properties
            )
            print(f"Tabelle '{full_table_name}' erfolgreich nach PostgreSQL geschrieben.")
        except Exception as e:
            print(f"Fehler bei der Verarbeitung von Tabelle '{tabelle_name}': {e}")

    spark.stop()
    print("\nAlle Gold-Tabellen erfolgreich in die Superset-Datenbank geladen.")

if __name__ == '__main__':
    main()