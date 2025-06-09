from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

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
    yaml_path = "/tmp/spark_app.yaml"
    with open(yaml_path, "w") as f:
        f.write(spark_app_yaml)
    os.system(f"kubectl apply -f {yaml_path}")

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
        rm -rf /tmp/your-private-repo || true
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        """
    )

    # Step 2: Submit SparkApplication using kubectl
    run_spark_job = PythonOperator(
        task_id='submit_spark_app',
        python_callable=submit_spark_job
    )

    clone_repo >> run_spark_job
