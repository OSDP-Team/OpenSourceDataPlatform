from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

#  Define your SparkApplication YAML (with PVC + PySpark path from repo)
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

with DAG("clone_and_run_spark_inline_yaml",
         start_date=datetime(2023, 1, 1),
         schedule_interval=None,
         catchup=False) as dag:

    #  Step 1: Clone GitHub repo with PySpark job
    clone_repo = BashOperator(
        task_id='clone_private_repo',
        bash_command="""
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        git clone https://${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        """
    )

    #  Step 2: Apply Spark job defined inline (via kubectl + heredoc)
    run_spark_job = BashOperator(
        task_id="submit_spark_app",
        bash_command=f'echo """{spark_app_yaml}""" | kubectl apply -f -'
    )

    clone_repo >> run_spark_job
