from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
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
            group="spark.stackable.tech", version="v1alpha1", plural="sparkapplications",
            body=self.application_file, namespace=self.namespace
        )

spark_app = {
    "apiVersion": "spark.stackable.tech/v1alpha1",
    "kind": "SparkApplication",
    "metadata": {"name": "spark-job", "namespace": "default"},
    "spec": {
        "sparkImage": {"productVersion": "3.5.5"},
        "mode": "cluster",
        "mainApplicationFile": "local:///tmp/your-private-repo/airflowDags/SparkTest.py",
        "driver": {"config": {"resources": {"memory": {"limit": "1Gi"}}}},
        "executor": {"replicas": 1, "config": {"resources": {"memory": {"limit": "2Gi"}}}}
    }
}

with DAG("spark_job", start_date=datetime(2023, 1, 1), schedule_interval=None, catchup=False) as dag:

    clone_repo = BashOperator(
        task_id='clone_repo',
        bash_command=
        bash_command= 
        """
        rm -rf /tmp/your-private-repo || true 
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}' 
        GIT_USER='{{ var.value.GIT_USER }}' 
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
         """ 
    )

    submit_spark_job = KubernetesPodOperator(
    submit_spark_job = SparkKubernetesOperator(
        task_id='submit_spark_job',
        name='spark-submitter',
        image='bitnami/kubectl:latest',
        cmds=['kubectl'],
        arguments=['apply', '-f', '-'],
        env_vars={'KUBECONFIG': '/var/run/secrets/kubernetes.io/serviceaccount'},
        in_cluster=True,
        body_template=str(spark_yaml).replace("'", '"')
        application_file=spark_app
    )

    clone_repo >> submit_spark_job
