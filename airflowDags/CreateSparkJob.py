from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from kubernetes.client import CustomObjectsApi
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
        namespace=namespace
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
