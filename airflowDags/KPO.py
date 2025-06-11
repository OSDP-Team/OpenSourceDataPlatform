from airflow import DAG
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime

# GitHub-Zugangsdaten aus Airflow Variables
git_user = Variable.get("GIT_USER")
git_token = Variable.get("GITHUB_TOKEN")

default_args = {
    "start_date": datetime(2023, 1, 1),
}

with DAG(
    dag_id="spark_job_k8s",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description="Spark Job aus GitHub Repo ausführen (ohne PVC)",
) as dag:

    spark_job = KubernetesPodOperator(
        task_id="run_spark_job",
        name="spark-job",
        namespace="default",
        image="bitnami/spark:3.5",  # Oder dein eigenes Spark-Image
        cmds=["sh", "-c"],
        arguments=[
            f"""
            git clone https://{git_user}:{git_token}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/repo && \
            /opt/bitnami/spark/bin/spark-submit /tmp/repo/airflowDags/SparkTest.py
            """
        ],
        get_logs=True,
        is_delete_operator_pod=True,
    )

    spark_job
