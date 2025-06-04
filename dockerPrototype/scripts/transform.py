import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../docker/.env'))

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# 1. SparkSession erstellen
spark = SparkSession.builder \
    .appName("Load CSV to PostgreSQL") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.2.27") \
    .getOrCreate()

# 2. CSV einlesen
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/Data.csv"))
df = spark.read \
    .option("header", True) \
    .option("sep", ";") \
    .option("inferSchema", True) \
    .csv(data_path)

# 3. Schema & Beispielzeilen anzeigen
df.printSchema()
df.show(5)

# 4. In PostgreSQL speichern
df.write \
    .format("jdbc") \
    .option("url", f"jdbc:postgresql://localhost:5432/{POSTGRES_DB}") \
    .option("dbtable", "testdaten") \
    .option("user", POSTGRES_USER) \
    .option("password", POSTGRES_PASSWORD) \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

with open("output/log.txt", "w") as log_file:
    log_file.write("CSV wurde erfolgreich gelesen und in die Datenbank geschrieben.\n")
    log_file.write(f"Tabelle: testdaten, Zeilenanzahl: {df.count()}\n")

spark.stop()