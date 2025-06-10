from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime

# SparkApplication YAML
spark_yaml = {
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
        """
        rm -rf /tmp/your-private-repo || true 
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}' 
        GIT_USER='{{ var.value.GIT_USER }}' 
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
         """ 
    )

    submit_spark_job = KubernetesPodOperator(
        task_id='submit_spark_job',
        name='spark-submitter',
        image='bitnami/kubectl:latest',
        cmds=['kubectl'],
        arguments=['apply', '-f', '-'],
        env_vars={'KUBECONFIG': '/var/run/secrets/kubernetes.io/serviceaccount'},
        in_cluster=True,
        body_template=str(spark_yaml).replace("'", '"')
    )

    clone_repo >> submit_spark_job
