from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from datetime import datetime
import re
import uuid
import time # Import time for polling

class SparkKubernetesOperator(BaseOperator):
    def __init__(self, application_file, namespace="default", delete_after_run=True, poll_interval=10, **kwargs):
        super().__init__(**kwargs)
        self.application_file = application_file
        self.namespace = namespace
        self.delete_after_run = delete_after_run
        self.poll_interval = poll_interval # Interval to poll for job status

    def execute(self, context):
        hook = KubernetesHook(conn_id="kubernetes_in_cluster")

        # Submit SparkApplication
        app = hook.create_custom_object(
            group="spark.stackable.tech",
            version="v1alpha1",
            plural="sparkapplications",
            body=self.application_file,
            namespace=self.namespace,
        )

        app_name = app['metadata']['name']
        self.log.info(f"Submitted SparkApplication: {app_name}")

        # Wait for job to finish
        self.log.info(f"Waiting for SparkApplication {app_name} to complete...")
        while True:
            current_app = hook.get_custom_object(
                group="spark.stackable.tech",
                version="v1alpha1",
                plural="sparkapplications",
                name=app_name,
                namespace=self.namespace,
            )
            application_state = current_app.get('status', {}).get('applicationState', {}).get('state')
            self.log.info(f"SparkApplication {app_name} current state: {application_state}")

            if application_state in ["COMPLETED", "FAILED", "UNKNOWN"]:
                if application_state == "COMPLETED":
                    self.log.info(f"SparkApplication {app_name} completed successfully.")
                else:
                    raise Exception(f"SparkApplication {app_name} failed with state: {application_state}")
                break
            time.sleep(self.poll_interval)

        # Delete the SparkApplication after execution
        if self.delete_after_run:
            self.log.info(f"Deleting SparkApplication: {app_name}")
            try:
                hook.delete_custom_object(
                    group="spark.stackable.tech",
                    version="v1alpha1",
                    plural="sparkapplications",
                    name=app_name,
                    namespace=self.namespace,
                )
                self.log.info(f"SparkApplication {app_name} deleted successfully.")
            except Exception as e:
                self.log.warning(f"Failed to delete SparkApplication {app_name}: {e}")
def sanitize_job_name(name: str) -> str:
    """
    Converts a script filename to a valid K8s resource name.
    """
    base = name.lower().replace(".py", "").replace("_", "-")
    # Remove all non-allowed characters
    base = re.sub(r"[^a-z0-9\-]", "", base)
    # Truncate to safe length (max 63 chars in K8s name)
    base = base[:50]
    # Append a short UUID suffix to ensure uniqueness
    suffix = uuid.uuid4().hex[:8]
    return f"sparkjob-{base}-{suffix}"

def generate_spark_manifest(script_filename: str) -> dict:
    job_name = sanitize_job_name(script_filename)
    return {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": job_name,
            "namespace": "default",
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

with DAG(
    "spark_stackable_job",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    description="Submit a Stackable SparkApplication via custom operator with auto-cleanup",
) as dag:

    bronze_to_silver_job = SparkKubernetesOperator(
        task_id="bronze_to_silver_job",
        application_file=generate_spark_manifest("bronze_to_silber.py")
    )

    silver_to_gold_job = SparkKubernetesOperator(
        task_id="silver_to_gold_job",
        application_file=generate_spark_manifest("silber_to_gold.py")
    )

    gold_to_postgres_job = SparkKubernetesOperator(
        task_id="gold_to_postgres_job",
        application_file=generate_spark_manifest("gold_to_postgres.py")
    )

    bronze_to_silver_job >> silver_to_gold_job >> gold_to_postgres_job