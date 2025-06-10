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


# Spark Application Configuration
spark_app = {
    "apiVersion": "spark.stackable.tech/v1alpha1",
    "kind": "SparkApplication",
    "metadata": {
        "name": "spark-job",
        "namespace": "default"
    },
    "spec": {
        # Spark Image Configuration
        "sparkImage": {
            "productVersion": "3.5.5"
        },
        
        # Execution Mode
        "mode": "cluster",
        
        # Main Application File
        "mainApplicationFile": "local:///tmp/your-private-repo/airflowDags/SparkTest.py",
        
        # Driver Configuration
        "driver": {
            "config": {
                # Resource Limits
                "resources": {
                    "memory": {"limit": "1Gi"}
                },
                
                # Init Container to Clone Repository
                "initContainers": [
                    {
                        "name": "git-clone",
                        "image": "alpine/git",
                        "command": ["sh", "-c"],
                        "args": [
                            "git clone https://$(GIT_USER):$(GIT_TOKEN)@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo"
                        ],
                        "env": [
                            {"name": "GIT_USER", "value": "your-username"},
                            {"name": "GIT_TOKEN", "value": "your-token"}
                        ],
                        "volumeMounts": [
                            {"name": "shared-data", "mountPath": "/tmp"}
                        ]
                    }
                ],
                
                # Volume Configuration
                "volumes": [
                    {"name": "shared-data", "emptyDir": {}}
                ],
                "volumeMounts": [
                    {"name": "shared-data", "mountPath": "/tmp"}
                ]
            }
        },
        
        # Executor Configuration
        "executor": {
            "replicas": 1,
            "config": {
                "resources": {
                    "memory": {"limit": "2Gi"}
                }
            }
        }
    }
}


# DAG Definition
with DAG(
    "spark_job", 
    start_date=datetime(2023, 1, 1), 
    schedule_interval=None, 
    catchup=False
) as dag:
    
    # Download Repository Task
    download_repo = BashOperator(
        task_id='download_repo',
        bash_command="""
        rm -rf /shared/your-private-repo || true
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}' 
        GIT_USER='{{ var.value.GIT_USER }}'
        curl -L -H "Authorization: token ${GIT_TOKEN}" \
             -o /shared/repo.zip \
             https://api.github.com/repos/NESuchi/Open-Source-Data-Platform/zipball/main
        cd /shared && unzip -q repo.zip
        mv /shared/NESuchi-Open-Source-Data-Platform-* /shared/your-private-repo
        rm /shared/repo.zip
        chmod -R 755 /shared/your-private-repo
        """
    )
    
    # Submit Spark Job Task
    submit_spark_job = SparkKubernetesOperator(
        task_id='submit_spark_job',
        application_file=spark_app
    )
    
    # Task Dependencies
    download_repo >> submit_spark_job
