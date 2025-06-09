from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime
import tempfile
import os

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

with DAG(
    "clone_and_run_spark_k8s_pod",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["spark", "kubernetes"],
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

    # Write spark_app_yaml to a temporary file on the Airflow worker, so we can mount it to the pod
    def write_yaml_to_tmp():
        tmp_dir = "/tmp/airflow_spark_app"
        os.makedirs(tmp_dir, exist_ok=True)
        path = os.path.join(tmp_dir, "sparkapplication.yaml")
        with open(path, "w") as f:
            f.write(spark_app_yaml)
        return path

    # Using a short PythonOperator just to write the YAML file, or you can do this manually beforehand
    from airflow.operators.python import PythonOperator
    write_yaml = PythonOperator(
        task_id="write_spark_yaml",
        python_callable=write_yaml_to_tmp,
    )

    submit_spark_app = KubernetesPodOperator(
        namespace='default',
        image="bitnami/kubectl:latest",
        cmds=["kubectl", "apply", "-f", "/sparkapplication.yaml"],
        name="submit-spark-application",
        task_id="submit_spark_application",
        get_logs=True,
        is_delete_operator_pod=True,
        volumes=[{
            "name": "spark-yaml-volume",
            "hostPath": {
                "path": "/tmp/airflow_spark_app",
                "type": "Directory"
            }
        }],
        volume_mounts=[{
            "name": "spark-yaml-volume",
            "mountPath": "/",
            "readOnly": True
        }],
        # optionally specify the service account name if you have one with proper RBAC permissions
        # service_account_name="airflow-k8s-sa",
    )

    clone_repo >> write_yaml >> submit_spark_app
