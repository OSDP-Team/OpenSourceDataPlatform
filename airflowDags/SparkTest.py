from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("MinimalTestJob").getOrCreate()

# Create a simple DataFrame
data = spark.range(0, 100)
count = data.count()

print(f"Total count is: {count}")
spark.stop()
