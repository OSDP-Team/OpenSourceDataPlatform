import os
from airflow import DAG
from airflow.models import BaseOperator
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
from kubernetes.client import CustomObjectsApi
from kubernetes.client.rest import ApiException
from datetime import datetime
import time
import logging

log = logging.getLogger(__name__)

def delete_spark_app(job_name, namespace="default", **kwargs):
    hook = KubernetesHook(conn_id="kubernetes_in_cluster")
    api = hook.get_conn()
    custom_api = CustomObjectsApi(api)

    try:
        log.info(f"Trying to delete SparkApplication '{job_name}' in namespace '{namespace}'")
        custom_api.delete_namespaced_custom_object(
            group="spark.stackable.tech",
            version="v1alpha1",
            namespace=namespace,
            plural="sparkapplications",
            name=job_name,
        )
        log.info(f"Successfully deleted SparkApplication '{job_name}'")
    except ApiException as e:
        if e.status == 404:
            log.info(f"SparkApplication '{job_name}' not found, skipping delete.")
        else:
            log.error(f"Error deleting SparkApplication '{job_name}': {e}")
            raise


class SparkKubernetesOperator(BaseOperator):
    def __init__(self, name, main_application_file, namespace="default", image=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.namespace = namespace
        self.main_application_file = main_application_file
        self.image = image or "ghcr.io/leartigashi/sparkrepoimage:latest"


    def execute(self, context):
        hook = KubernetesHook()
        api: CustomObjectsApi = hook.get_conn()
        body = {
                "apiVersion": "spark.stackable.tech/v1alpha1",
                "kind": "SparkApplication",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace
                },
                "spec": {
                    "image": self.image,
                    "sparkImage": {
                        "productVersion": "3.5.5",
                        "pullSecrets": [
                            {"name": "ghcr-secret"}
                        ]
                    },
                    "mode": "cluster",
                    "mainApplicationFile": self.main_application_file,
                    "env": [
                        {
                            "name": "MINIO_ACCESS_KEY",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "minio-secret",
                                    "key": "MINIO_ACCESS_KEY"
                                }
                            }
                        },
                        {
                            "name": "MINIO_SECRET_KEY",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "minio-secret",
                                    "key": "MINIO_SECRET_KEY"
                                }
                            }
                        }
                    ],
                    "sparkConf": {
                        "spark.jars": "https://jdbc.postgresql.org/download/postgresql-42.7.3.jar"
                    },
                    "driver": {
                        "config": {
                            "resources": {
                                "cpu": {
                                    "min": "1",
                                    "max": "2"
                                },
                                "memory": {
                                    "limit": "1Gi"
                                }
                            }
                        }
                    },
                    "executor": {
                        "replicas": 1,
                        "config": {
                            "resources": {
                                "cpu": {
                                    "min": "1",
                                    "max": "2"
                                },
                                "memory": {
                                    "limit": "1Gi"
                                }
                            }
                        }
                    }
                }
            }
        
        log.info(f"Creating SparkApplication {self.name}")
        api.create_namespaced_custom_object(
            group="spark.stackable.tech",
            version="v1alpha1",
            namespace=self.namespace,
            plural="sparkapplications",
            body=body
        )

        log.info(f"Waiting for SparkApplication {self.name} to complete...")
        while True:
            time.sleep(10)
            app = api.get_namespaced_custom_object(
                group="spark.stackable.tech",
                version="v1alpha1",
                namespace=self.namespace,
                plural="sparkapplications",
                name=self.name
            )
            status = app.get("status", {}).get("applicationState", {}).get("state", "UNKNOWN")
            log.info(f"SparkApplication {self.name} current state: {status}")
            if status in ["COMPLETED", "FAILED"]:
                break

        if status == "FAILED":
            raise Exception(f"SparkApplication {self.name} failed.")

        log.info(f"SparkApplication {self.name} completed successfully.")
    


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


with DAG(
    dag_id="spark_sequential_jobs",
    start_date=datetime(2025, 7, 2),
    schedule_interval=None,
    catchup=False
) as dag:
    
    cleanup_bronze = PythonOperator(
    task_id="cleanup_bronze_to_silver",
    python_callable=delete_spark_app,
    op_kwargs={"job_name": "sparkjob-bronze-to-silver"}
    )

    bronze_to_silver = SparkKubernetesOperator(
        task_id="bronze_to_silver",
        name="sparkjob-bronze-to-silver",
        main_application_file="local:///stackable/spark/jobs/bronze_to_silver.py",
    )
    
    cleanup_silver = PythonOperator(
        task_id="cleanup_silver_to_gold",
        python_callable=delete_spark_app,
        op_kwargs={"job_name": "sparkjob-silver-to-gold"}
    )

    silver_to_gold = SparkKubernetesOperator(
        task_id="silver_to_gold",
        name="sparkjob-silver-to-gold",
        main_application_file="local:///stackable/spark/jobs/silver_to_gold.py",
    )

    cleanup_gold = PythonOperator(
        task_id="cleanup_silver_to_gold",
        python_callable=delete_spark_app,
        op_kwargs={"job_name": "sparkjob-gold-to-postgres"}
    )

    gold_to_postgres = SparkKubernetesOperator(
        task_id="gold-to-postgres",
        name="sparkjob-gold-to-postgres",
        main_application_file="local:///stackable/spark/jobs/gold_to_postgres.py",
    )




    cleanup_bronze >> bronze_to_silver >> cleanup_silver >> silver_to_gold >> cleanup_gold >> gold_to_postgres
