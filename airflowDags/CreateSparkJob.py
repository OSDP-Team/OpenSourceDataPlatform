from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from datetime import datetime


class SparkKubernetesOperator(BaseOperator):
    def __init__(self, application_file, namespace="default", delete_after_run=True, **kwargs):
        super().__init__(**kwargs)
        self.application_file = application_file
        self.namespace = namespace
        self.delete_after_run = delete_after_run

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

        # Wait for job to finish (optional: implement polling logic here if needed)
        # Here you could wait for success/failed status...

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
            except Exception as e:
                self.log.warning(f"Failed to delete SparkApplication {app_name}: {e}")

def generate_spark_manifest(script_filename: str) -> dict:
    return {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": "sparkjob-" + script_filename.replace(".py", ""),
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
