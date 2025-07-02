import os
from airflow import DAG
from airflow.models import BaseOperator
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from kubernetes.client import CustomObjectsApi
from kubernetes.client.rest import ApiException
from datetime import datetime


class SparkKubernetesOperator(BaseOperator):
    def __init__(self, application_file, namespace="default", **kwargs):
        super().__init__(**kwargs)
        self.application_file = application_file
        self.namespace = namespace

    def execute(self, context):
        hook = KubernetesHook(conn_id="kubernetes_in_cluster")
        return hook.create_custom_object(
            group="spark.stackable.tech",
            version="v1alpha1",
            plural="sparkapplications",
            body=self.application_file,
            namespace=self.namespace,
        )


def delete_spark_app(job_name, namespace="default", **kwargs):
    hook = KubernetesHook(conn_id="kubernetes_in_cluster")
    api = hook.get_conn()
    custom_api = CustomObjectsApi(api)

    try:
        custom_api.delete_namespaced_custom_object(
            group="spark.stackable.tech",
            version="v1alpha1",
            namespace=namespace,
            plural="sparkapplications",
            name=job_name,
        )
        print(f"Deleted SparkApplication {job_name}")
    except ApiException as e:
        if e.status == 404:
            print(f"SparkApplication {job_name} not found, skipping delete")
        else:
            raise


def build_spark_manifest(job_name, script_path):
    resources = {
        "cpu": {"min": "1", "max": "2"},
        "memory": {"limit": "1Gi"}
    }

    return {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": job_name,
            "namespace": "default"
        },
        "spec": {
            "image": "ghcr.io/leartigashi/sparkrepoimage:latest",
            "sparkImage": {
                "productVersion": "3.5.5",
                "pullSecrets": [{"name": "ghcr-secret"}]
            },
            "mode": "cluster",
            "mainApplicationFile": script_path,
            "driver": {"config": {"resources": resources}},
            "executor": {
                "replicas": 1,
                "config": {"resources": resources}
            }
        }
    }


with DAG(
    "spark_stackable_multi_job",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    description="Run multiple Stackable Spark jobs via custom operator",
) as dag:

    script_paths = [
        "local:///stackable/spark/jobs/bronze_to_silber.py",
        "local:///stackable/spark/jobs/silber_to_gold.py",
        "local:///stackable/spark/jobs/gold_to_postgres.py"
    ]

    def sanitize_job_name(script_filename: str) -> str:
        name = os.path.splitext(script_filename)[0]  
        name = name.lower().replace("_", "-")
        return name.strip("-")                        

    cleanup_tasks = []
    submit_tasks = []

    for script_path in script_paths:
        script_filename = os.path.basename(script_path)
        job_name = sanitize_job_name(script_filename)

        cleanup_task = PythonOperator(
            task_id=f"cleanup_{job_name}",
            python_callable=delete_spark_app,
            op_kwargs={"job_name": job_name}
        )
        cleanup_tasks.append(cleanup_task)

        spark_manifest = build_spark_manifest(job_name, script_path)

        submit_task = SparkKubernetesOperator(
            task_id=f"submit_{job_name}",
            application_file=spark_manifest
        )
        submit_tasks.append(submit_task)

        cleanup_task >> submit_task

    # Jetzt kette die Jobs nacheinander
    for i in range(len(submit_tasks) - 1):
        submit_tasks[i] >> cleanup_tasks[i + 1]