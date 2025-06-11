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
        "mainApplicationFile": "local:///shared/SparkTest.py",  # verwendet Datei aus PVC
        "volumes": [
            {
                "name": "shared-volume",
                "persistentVolumeClaim": {
                    "claimName": "shared-spark-pvc"
                }
            }
        ],
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
            },
            "volumeMounts": [
                {
                    "name": "shared-volume",
                    "mountPath": "/shared"
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
                    "cpu": {
                        "min": "1",
                        "max": "2"
                    },
                    "memory": {
                        "limit": "1Gi"
                    }
                }
            },
            "volumeMounts": [
                {
                    "name": "shared-volume",
                    "mountPath": "/shared"
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
        bash_command="""
        kubectl delete sparkapplication spark-job -n default || true
        """,
    )
    
    clone_repo = BashOperator(
    task_id='clone_repo',
    bash_command="""
    mkdir -p /tmp/gitclone
    cd /tmp/gitclone
    
    GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}' 
    GIT_USER='{{ var.value.GIT_USER }}' 
        
    git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git 
        
    ls -l Open-Source-Data-Platform
    ls -l Open-Source-Data-Platform/airflowDags
        
    echo "User info:"
    whoami
    id
        
    echo "Vor dem Kopieren, Inhalt /shared:"
    ls -la /shared
        
    cp Open-Source-Data-Platform/airflowDags/*.py /shared/ || { echo "Copy failed"; exit 1; }
        
    echo "Nach dem Kopieren, Inhalt /shared:"
    ls -la /shared
        
    rm -rf /tmp/gitclone
        
    if [ ! -f /shared/SparkTest.py ]; then
    echo "Fehler: SparkTest.py wurde nicht rechtzeitig gefunden"
    exit 1
    fi
    """
    )
    
    submit_spark_job = SparkKubernetesOperator(
        task_id='submit_spark_job',
        application_file=spark_app
    )
    
    cleanup_task >> clone_repo >> submit_spark_job
