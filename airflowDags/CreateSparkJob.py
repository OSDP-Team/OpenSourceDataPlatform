from airflow import DAG
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
            namespace=self.namespace
        )

# SparkApplication mit ConfigMap statt PVC
spark_app = {
    "apiVersion": "spark.stackable.tech/v1alpha1",
    "kind": "SparkApplication",
    "metadata": {
        "name": "spark-job",
        "namespace": "default"
    },
    "spec": {
        "sparkImage": {"productVersion": "3.5.5"},
        "mode": "cluster",
        "mainApplicationFile": "local:///opt/spark/scripts/SparkTest.py",
        "volumes": [
            {
                "name": "script-volume",
                "configMap": {
                    "name": "spark-script"
                }
            }
        ],
        "driver": {
            "config": {
                "resources": {
                    "memory": {"limit": "1Gi"}
                }
            },
            "volumeMounts": [
                {
                    "name": "script-volume",
                    "mountPath": "/opt/spark/scripts"
                }
            ],
            "securityContext": {
                "fsGroup": 1000
            }
        },
        "executor": {
            "replicas": 1,
            "config": {
                "resources": {
                    "memory": {"limit": "2Gi"}
                }
            },
            "volumeMounts": [
                {
                    "name": "script-volume",
                    "mountPath": "/opt/spark/scripts"
                }
            ],
            "securityContext": {
                "fsGroup": 1000
            }
        }
    }
}

with DAG("spark_job", start_date=datetime(2023, 1, 1), schedule_interval=None, catchup=False) as dag:

    cleanup_task = BashOperator(
        task_id='cleanup_previous_spark_job',
        bash_command="kubectl delete sparkapplication spark-job -n default || true"
    )

    clone_and_create_configmap = BashOperator(
        task_id='clone_and_create_configmap',
        bash_command="""
        rm -rf /tmp/gitclone
        mkdir -p /tmp/gitclone
        cd /tmp/gitclone

        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'

        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git

        cd Open-Source-Data-Platform/airflowDags

        if [ ! -f SparkTest.py ]; then
            echo "SparkTest.py nicht gefunden!"
            exit 1
        fi

        kubectl create configmap spark-script --from-file=SparkTest.py=./SparkTest.py -n default --dry-run=client -o yaml | kubectl apply -f -
        """
    )

    submit_spark_job = SparkKubernetesOperator(
        task_id='submit_spark_job',
        application_file=spark_app
    )

    cleanup_task >> clone_and_create_configmap >> submit_spark_job
