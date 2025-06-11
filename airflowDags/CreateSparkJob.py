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


with DAG("spark_job", start_date=datetime(2023, 1, 1), schedule_interval=None, catchup=False) as dag:

    git_user = Variable.get("GIT_USER")
    git_token = Variable.get("GITHUB_TOKEN")

    spark_app = {
        "apiVersion": "spark.stackable.tech/v1alpha1",
        "kind": "SparkApplication",
        "metadata": {
            "name": "spark-job",
            "namespace": "default"
        },
        "spec": {
            "sparkImage": {
                "productVersion": "3.5.5"
            },
            "mode": "cluster",
            "mainApplicationFile": "local:///tmp/SparkTest.py",
            "volumes": [
                {
                    "name": "shared-volume",
                    "emptyDir": {}
                }
            ],
            "driver": {
                "volumes": [
                    {
                        "name": "shared-volume",
                        "emptyDir": {}
                    }
                ],
                "initContainers": [
                    {
                        "name": "git-clone",
                        "image": "alpine/git",
                        "env": [
                            {"name": "GIT_USER", "value": git_user},
                            {"name": "GIT_TOKEN", "value": git_token},
                        ],
                        "command": [
                            "sh",
                            "-c",
                            "git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/code && cp /tmp/code/airflowDags/SparkTest.py /tmp/"
                        ],
                        "volumeMounts": [
                            {
                                "mountPath": "/tmp",
                                "name": "shared-volume"
                            }
                        ]
                    }
                ],
                "volumeMounts": [
                    {
                        "mountPath": "/tmp",
                        "name": "shared-volume"
                    }
                ],
                "config": {
                    "resources": {
                        "cpu": {"min": "1", "max": "2"},
                        "memory": {"limit": "1Gi"},
                    }
                },
                "securityContext": {"fsGroup": 1000},
            },
            "executor": {
                "replicas": 1,
                "config": {
                    "resources": {
                        "cpu": {"min": "1", "max": "2"},
                        "memory": {"limit": "1Gi"},
                    }
                },
                "securityContext": {"fsGroup": 1000},
            },
        },
    }

    cleanup_task = BashOperator(
        task_id='cleanup_previous_spark_job',
        bash_command="kubectl delete sparkapplication spark-job -n default || true"
    )

    submit_spark_job = SparkKubernetesOperator(
        task_id='submit_spark_job',
        application_file=spark_app
    )

    cleanup_task >> submit_spark_job
