from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
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


with DAG(
    "spark_stackable_job",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    description="Submit a Stackable SparkApplication via custom operator",
) as dag:

    cleanup_task = BashOperator(
        task_id="cleanup_previous_spark_job",
        bash_command="kubectl delete sparkapplication pysparktest-job -n default || true"
    )
    resources = {
        "cpu": {"min": "1", "max": "2"},
        "memory": {"limit": "1Gi"}
    }
    spark_app = {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": "pysparktest-job",
            "namespace": "default"
        },
        "spec": {
            "image": "ghcr.io/leartigashi/sparkrepoimage:latest",
            "sparkImage": {
                "productVersion": "3.5.5",
                "pullSecrets": [{"name": "ghcr-secret"}]
            },
            "mode": "cluster",
            "mainApplicationFile": "local:///stackable/spark/jobs/hierstarten.py",
            "driver": {"config": {"resources": resources}},
            "executor": {
                "replicas": 1,
                "config": {"resources": resources}
            }
        }
    }

    submit_spark_job = SparkKubernetesOperator(
        task_id="submit_spark_job",
        application_file=spark_app
    )

    cleanup_task >> submit_spark_job
