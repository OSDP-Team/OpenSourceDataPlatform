from pyspark.sql.types import StructType, StructField, StringType

def read_data(spark, config):
    """Liest Daten basierend auf der Source-Konfiguration."""
    source_conf = config['source']
    path = source_conf['path']
    format = source_conf['format']
    options = source_conf.get('options', {})

    # Schema aus der Konfiguration bauen, falls vorhanden
    if 'schema' in config:
        schema_def = config['schema']
        # Einfache Implementierung, die erstmal alle Typen als String liest
        # Die Transformation kümmert sich um das korrekte Casting
        struct_schema = StructType([StructField(k, StringType(), True) for k in schema_def.keys()])
        return spark.read.format(format).options(**options).schema(struct_schema).load(path)
    else:
        # Fallback auf inferSchema, wenn kein Schema definiert ist
        return spark.read.format(format).options(**options).load(path)