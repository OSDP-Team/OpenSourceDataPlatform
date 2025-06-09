from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime
import yaml
import logging

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
    # Kubernetes Config laden (im Cluster oder local)
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    # YAML in Python dict parsen
    spark_app = yaml.safe_load(spark_app_yaml)

    # CustomObjects API benutzen
    api = client.CustomObjectsApi()

    group = "spark.stackable.tech"
    version = "v1alpha1"
    namespace = "default"
    plural = "sparkapplications"

    try:
        # SparkApplication erstellen
        api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            body=spark_app
        )
        logging.info("SparkApplication created successfully")
    except ApiException as e:
        if e.status == 409:
            logging.info("SparkApplication already exists, updating it")
            api.replace_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=spark_app["metadata"]["name"],
                body=spark_app
            )
        else:
            logging.error(f"Failed to create SparkApplication: {e}")
            raise

with DAG(
    "clone_and_run_spark_inline_yaml",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    clone_repo = BashOperator(
        task_id='clone_private_repo',
        bash_command="""
        rm -rf /tmp/your-private-repo || true
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        """
    )

    run_spark_job = PythonOperator(
        task_id='submit_spark_app',
        python_callable=submit_spark_job
    )

    clone_repo >> run_spark_job
