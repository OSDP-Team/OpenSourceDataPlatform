from airflow import DAGAdd commentMore actions
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
from kubernetes import client, config
from kubernetes.utils import create_from_dict
import yaml

#  Define your SparkApplication YAML (with PVC + PySpark path from repo)
# Define your SparkApplication YAML
spark_app_yaml = """
apiVersion: spark.stackable.tech/v1alpha1
kind: SparkApplication
@@ -33,27 +37,34 @@
        claimName: shared-spark-pvc
"""

with DAG("clone_and_run_spark_inline_yaml",
         start_date=datetime(2023, 1, 1),
         schedule_interval=None,
         catchup=False) as dag:
def submit_spark_job():
    # Load Kubernetes cluster config from within the Airflow pod
    config.load_incluster_config()
    api_client = client.ApiClient()
    doc = yaml.safe_load(spark_app_yaml)
    create_from_dict(api_client, doc)

    #  Step 1: Clone GitHub repo with PySpark job
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
        echo "User: $GIT_USER"
        echo "Token length: ${#GIT_TOKEN}"
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        """
    )

    #  Step 2: Apply Spark job defined inline (via kubectl + heredoc)
    run_spark_job = BashOperator(
        task_id="submit_spark_app",
        bash_command=f'echo """{spark_app_yaml}""" | kubectl apply -f -'
    # Step 2: Submit Spark job to Stackable Spark Operator
    run_spark_job = PythonOperator(
        task_id='submit_spark_app',
        python_callable=submit_spark_job
    )

    clone_repo >> run_spark_job
