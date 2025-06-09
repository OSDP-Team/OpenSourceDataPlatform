from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
from kubernetes import client, config
from kubernetes.utils import create_from_dict
import yaml

# Define your SparkApplication YAML
spark_app_yaml = """
apiVersion: spark.stackable.tech/v1alpha1
kind: SparkApplication
metadata:
  name: airflow-spark-job
  namespace: default
spec:
  mode: cluster
  mainApplicationFile: local:///tmp/your-private-repo/airflowDags/SparkTest.py
  sparkImage:
    image: ghcr.io/stackable/spark:3.4.1-debian-11-r0
  driver:
    cores: 1
    memory: "1g"
    volumeMounts:
      - name: shared-volume
        mountPath: /shared
  executor:
    cores: 1
    memory: "2g"
    instances: 1
    volumeMounts:
      - name: shared-volume
        mountPath: /shared
  volumes:
    - name: shared-volume
      persistentVolumeClaim:
        claimName: shared-spark-pvc
"""

def submit_spark_job():
    # Load Kubernetes cluster config from within the Airflow pod
    config.load_incluster_config()
    api_client = client.ApiClient()
    doc = yaml.safe_load(spark_app_yaml)
    create_from_dict(api_client, doc)

with DAG(
    "clone_and_run_spark_inline_yaml",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    # Step 1: Clone GitHub repo with PySpark job
    clone_repo = BashOperator(
        task_id='clone_private_repo',
        bash_command="""
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        """
    )

    # Step 2: Submit Spark job to Stackable Spark Operator
    run_spark_job = PythonOperator(
        task_id='submit_spark_app',
        python_callable=submit_spark_job
    )

    clone_repo >> run_spark_job
