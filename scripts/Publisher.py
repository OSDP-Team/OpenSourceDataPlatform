from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from datetime import datetime, timedelta
import os
import re

def extract_metadata_from_filename(filename: str):
    """
    Extrahiert 'modul' und 'intervall' aus einem Dateinamen.
    Beispiel: a_Strom_GOM_M2_15min_kWh_20220101000000_20230101000000
    """
    match = re.match(r"a_([\w]+(?:_[\w]+)*)_(\d+min)_", filename)
    if not match:
        raise ValueError(f"Dateiname {filename} ist ungültig oder entspricht nicht dem erwarteten Format.")
    modul = match.group(1)
    intervall = match.group(2)
    return modul, intervall

def generate_spark_dataframe(spark, start_time: datetime, num_rows: int, modul: str, intervall: str):
    """
    Erzeugt ein PySpark DataFrame mit simulierten Messwerten.
    """
    rows = []
    current_time = start_time

    for _ in range(num_rows):
        min_val = round(np.random.normal(0.151, 0.0005), 6)
        max_val = round(min_val + np.random.uniform(0.0002, 0.001), 6)
        avg_val = round((min_val + max_val) / 2, 6)
        sum_val = round(avg_val, 6)
        pval = round(np.random.normal(0.605, 0.002), 6)

        row = (
            50, 0, 0,
            current_time.strftime("%d.%m.%Y %H:%M"),
            min_val, (current_time - timedelta(minutes=15)).strftime("%d.%m.%Y %H:%M"),
            max_val, (current_time - timedelta(minutes=15)).strftime("%d.%m.%Y %H:%M"),
            avg_val, sum_val, pval,
            1, "01.01.0001 00:00:00", "",  # OFFSET, VERSION, TEXT
            modul, intervall, 1, 0         # MESS_ID, COMP_LEVEL
        )
        rows.append(row)
        current_time += timedelta(minutes=15)

    schema = StructType([
        StructField("STATE_VAL", IntegerType()),
        StructField("STATE_ACQ", IntegerType()),
        StructField("STATE_COR", IntegerType()),
        StructField("ENTRYDATE", StringType()),
        StructField("MIN", DoubleType()),
        StructField("MINDATE", StringType()),
        StructField("MAX", DoubleType()),
        StructField("MAXDATE", StringType()),
        StructField("AVG", DoubleType()),
        StructField("SUM", DoubleType()),
        StructField("PVALUE", DoubleType()),
        StructField("OFFSET", IntegerType()),
        StructField("VERSION", StringType()),
        StructField("TEXT", StringType()),
        StructField("modul", StringType()),
        StructField("intervall", StringType()),
        StructField("MESS_ID", IntegerType()),
        StructField("COMP_LEVEL", IntegerType()),
    ])

    return spark.createDataFrame(rows, schema)

def main():
    # Beispiel-Dateiname (realistisch in der Pipeline)
    filename = "a_Strom_GOM_M2_15min_kWh_20220101000000_20230101000000"

    modul, intervall = extract_metadata_from_filename(filename)

    minio_user = os.getenv("MINIO_ACCESS_KEY")
    minio_pwd = os.getenv("MINIO_SECRET_KEY")

    if not minio_user or not minio_pwd:
        raise ValueError("MINIO_ACCESS_KEY oder MINIO_SECRET_KEY nicht gesetzt")

    spark = (
        SparkSession.builder
            .appName("simulate-publisher-spark")
            .master("local[*]")
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.688")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.access.key", minio_user)
            .config("spark.hadoop.fs.s3a.secret.key", minio_pwd)
            .getOrCreate()
    )

    start_time = datetime.strptime("01.01.2022 00:00", "%d.%m.%Y %H:%M")
    df = generate_spark_dataframe(spark, start_time, num_rows=96, modul=modul, intervall=intervall)

    output_path = f"s3a://producer/{filename}.csv"

    df.write \
        .mode("overwrite") \
        .option("header", True) \
        .option("sep", ";") \
        .csv(output_path)

    print(f"Synthetische Daten erfolgreich geschrieben nach: {output_path}")

    spark.stop()

if __name__ == "__main__":
    import numpy as np
    main()
