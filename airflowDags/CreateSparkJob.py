from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from datetime import datetime
import re
import uuid
import time # Für polling
import logging # Für Logs im Operator

log = logging.getLogger(__name__)

class SparkKubernetesOperator(BaseOperator):
    def __init__(self, spark_manifest: dict, namespace="default", poll_interval=10, **kwargs):
        super().__init__(**kwargs)
        self.spark_manifest = spark_manifest
        self.namespace = namespace
        self.poll_interval = poll_interval
        self.job_name = spark_manifest["metadata"]["name"]
        self.manifest_namespace = spark_manifest["metadata"].get("namespace", namespace)


    def execute(self, context):
        hook = KubernetesHook(conn_id=None) 
        api_client = hook.api_client
        custom_objects_api = api_client.CustomObjectsApi()

        log.info(f"Attempting to create SparkApplication: {self.job_name} in namespace: {self.manifest_namespace}")

        try:
            custom_objects_api.create_namespaced_custom_object(
                group="spark.stackable.tech",
                version="v1alpha1",
                namespace=self.manifest_namespace,
                plural="sparkapplications", 
                body=self.spark_manifest,
            )
            log.info(f"SparkApplication {self.job_name} created successfully.")

            # 2. Status überwachen
            status = "UNKNOWN"
            while status not in ["Completed", "Failed"]: # Stackable states
                try:
                    spark_app = custom_objects_api.get_namespaced_custom_object(
                        group="spark.stackable.tech",
                        version="v1alpha1",
                        namespace=self.manifest_namespace,
                        plural="sparkapplications",
                        name=self.job_name,
                    )
                    status = spark_app.get("status", {}).get("applicationState", {}).get("state", "UNKNOWN")
                    log.info(f"SparkApplication {self.job_name} current state: {status}")

                    if status == "Completed":
                        log.info(f"SparkApplication {self.job_name} completed successfully.")
                        break
                    elif status == "Failed":
                        log.error(f"SparkApplication {self.job_name} failed.")
                        # Optional: Fetch detailed error message from status.applicationState.errorMessage
                        error_message = spark_app.get("status", {}).get("applicationState", {}).get("errorMessage", "No specific error message.")
                        raise Exception(f"SparkApplication {self.job_name} failed: {error_message}")
                    elif status in ["Unkown", "Pending", "Submitted", "Running"]:
                        time.sleep(self.poll_interval)
                    else: # Handle unexpected states if any
                        log.warning(f"SparkApplication {self.job_name} in unexpected state: {status}. Waiting...")
                        time.sleep(self.poll_interval)

                except Exception as e:
                    log.error(f"Error while polling SparkApplication {self.job_name}: {e}")
                    raise

        except Exception as e:
            log.error(f"Error creating SparkApplication {self.job_name}: {e}")
            # Optional: Überprüfen, ob es sich um "already exists" handelt und diesen Fall speziell behandeln
            # although with dynamic names, this should rarely happen for the first creation attempt.
            raise


def sanitize_job_name(name: str) -> str:
    """
    Converts a script filename to a valid K8s resource name.
    """
    base = name.lower().replace(".py", "").replace("_", "-")
    # Remove all non-allowed characters
    base = re.sub(r"[^a-z0-9\-.]", "", base) # Erlaube auch Punkte, falls im Skriptnamen relevant
    # Truncate to safe length (max 63 chars in K8s name)
    # Behalte genug Platz für den Suffix und das Präfix
    max_base_len = 63 - len("sparkjob--") - 8 # 63 - Präfix - Suffix Länge
    base = base[:max_base_len]
    # Append a short UUID suffix to ensure uniqueness
    suffix = uuid.uuid4().hex[:8]
    return f"sparkjob-{base}-{suffix}"

def generate_spark_manifest(script_filename: str, namespace: str = "default") -> dict:
    job_name = sanitize_job_name(script_filename)
    
    manifest = {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": job_name,
            "namespace": namespace, # Namespace hier setzen
        },
        "spec": {
            "image": "ghcr.io/leartigashi/sparkrepoimage:latest",
            "sparkImage": {
                "productVersion": "3.5.5",
                "pullSecrets": [{"name": "ghcr-secret"}],
            },
            "mode": "cluster",
            "mainApplicationFile": f"local:///stackable/spark/jobs/{script_filename}",
            "env": [
                {
                    "name": "MINIO_ACCESS_KEY",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": "minio-secret",
                            "key": "MINIO_ACCESS_KEY",
                        }
                    },
                },
                {
                    "name": "MINIO_SECRET_KEY",
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": "minio-secret",
                            "key": "MINIO_SECRET_KEY",
                        }
                    },
                },
            ],
            "driver": {
                "config": {
                    "resources": {
                        "cpu": {"min": "1", "max": "2"},
                        "memory": {"limit": "1Gi"},
                    }
                }
            },
            "executor": {
                "replicas": 1,
                "config": {
                    "resources": {
                        "cpu": {"min": "1", "max": "2"},
                        "memory": {"limit": "1Gi"},
                    }
                },
            },
            # Hinzufügen der Cleanup-Sektion für den Stackable Spark Operator
            "cleanup": {
                "type": "Delete", # Dies ist der Standard für automatische Löschung
                # "ttlSecondsAfterFinished": 300 # Optional: Behält die CRD für 5 Minuten nach Abschluss
            }
        },
    }
    return manifest


with DAG(
    "spark_stackable_job",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    description="Submit a Stackable SparkApplication via custom operator with auto-cleanup",
) as dag:

    # Generiere Manifeste für jeden Task, um einen eindeutigen Job-Namen zu gewährleisten
    # und übergebe sie direkt an den Operator
    namespace = "default" # Oder den tatsächlichen Namespace Ihrer Spark-Jobs

    bronze_to_silver_manifest = generate_spark_manifest("bronze_to_silber.py", namespace=namespace)
    silver_to_gold_manifest = generate_spark_manifest("silber_to_gold.py", namespace=namespace)
    gold_to_postgres_manifest = generate_spark_manifest("gold_to_postgres.py", namespace=namespace)


    bronze_to_silver_job = SparkKubernetesOperator(
        task_id="bronze_to_silver_job",
        spark_manifest=bronze_to_silver_manifest,
        namespace=namespace # Redundant, wenn im Manifest gesetzt, aber zur Klarheit
    )

    silver_to_gold_job = SparkKubernetesOperator(
        task_id="silver_to_gold_job",
        spark_manifest=silver_to_gold_manifest,
        namespace=namespace
    )

    gold_to_postgres_job = SparkKubernetesOperator(
        task_id="gold_to_postgres_job",
        spark_manifest=gold_to_postgres_manifest,
        namespace=namespace
    )

    bronze_to_silver_job >> silver_to_gold_job >> gold_to_postgres_job
